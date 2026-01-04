from uuid import UUID
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile

from app.models.item import Item
from app.models.document import Document
from app.models.document_revision import DocumentRevision
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.models.project_section import ProjectSection
from app.services.project_service import get_or_create_section
from app.services.file_storage_service import save_file, delete_file
from app.utils.filename_parser import parse_filename
from app.utils.validators import validate_pdf_header


def notify_item_imported(
    db: Session,
    item: Item,
    responsible_id: Optional[UUID]
) -> None:
    """Notify responsible user and admins about imported item."""
    message = f"Новое изделие '{item.name}' ({item.part_number}) импортировано"
    payload = {
        "item_id": str(item.id),
        "part_number": item.part_number,
        "name": item.name,
    }
    
    # Notify responsible user
    if responsible_id:
        notification = Notification(
            user_id=responsible_id,
            message=message,
            event_payload=payload,
        )
        db.add(notification)
    
    # Notify all admins
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active == True).all()
    for admin in admins:
        # Don't notify if admin is the responsible user (avoid duplicate)
        if responsible_id and admin.id == responsible_id:
            continue
        notification = Notification(
            user_id=admin.id,
            message=message,
            event_payload=payload,
        )
        db.add(notification)


async def import_items_from_files(
    db: Session,
    project_id: UUID,
    files: List[UploadFile],
    section_id: Optional[UUID],
    responsible_id: Optional[UUID],
    current_user: User
) -> Dict[str, Any]:
    """
    Import items from uploaded PDF files.
    
    Single atomic transaction for all files.
    
    Returns:
        {"created_count": int, "errors": List[{"filename": str, "error": str}]}
    """
    created_count = 0
    errors: List[Dict[str, str]] = []
    saved_files: List[UUID] = []  # Track saved files for cleanup on error
    
    # Validate section_id belongs to project_id (early validation before any file processing)
    if section_id is not None:
        section = db.query(ProjectSection).filter(
            ProjectSection.id == section_id,
            ProjectSection.project_id == project_id
        ).first()
        
        if not section:
            return {
                "created_count": 0,
                "errors": [{"filename": "batch", "error": f"Section with id '{section_id}' not found or does not belong to project '{project_id}'"}],
            }
    
    try:
        for file in files:
            filename = file.filename or "unnamed.pdf"
            
            try:
                # Step 1: Validate PDF header (skip file if invalid)
                try:
                    await validate_pdf_header(file)
                except Exception as e:
                    errors.append({"filename": filename, "error": f"Invalid PDF: {str(e)}"})
                    continue
                
                # Step 2: Parse filename (non-blocking)
                parsed = parse_filename(filename)
                parsed_section_code = parsed.get("section_code")
                parsed_part_number = parsed.get("part_number")
                parsed_name = parsed.get("name") or filename
                
                # Step 3: Determine section_id
                effective_section_id = section_id
                if not effective_section_id and parsed_section_code:
                    # Auto-detect section from parsed_section_code
                    # Use commit=False to defer commit to batch transaction
                    section = get_or_create_section(db, project_id, parsed_section_code, commit=False)
                    if section:
                        effective_section_id = section.id
                
                # Step 4: Determine part_number
                # If part_number is None after parsing, use filename as part_number
                effective_part_number = parsed_part_number
                if not effective_part_number:
                    # Generate from filename (remove extension, replace spaces)
                    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    effective_part_number = base_name.replace(' ', '_')[:100]
                
                # Step 5: Check for duplicate part_number in database
                existing_item = db.query(Item).filter(
                    Item.part_number == effective_part_number
                ).first()
                
                if existing_item:
                    errors.append({"filename": filename, "error": f"Part number '{effective_part_number}' already exists"})
                    continue
                
                # Step 6: Create Item
                item = Item(
                    project_id=project_id,
                    section_id=effective_section_id,
                    part_number=effective_part_number,
                    name=parsed_name,
                    responsible_id=responsible_id,
                )
                db.add(item)
                db.flush()  # Get item ID
                
                # Step 7: Save file using save_file
                file_info = await save_file(file)
                saved_files.append(file_info["uuid"])
                
                # Step 8: Create Document with title = item.name
                document = Document(
                    item_id=item.id,
                    title=item.name,
                )
                db.add(document)
                db.flush()  # Get document ID
                
                # Step 9: Create DocumentRevision with label "-"
                revision = DocumentRevision(
                    document_id=document.id,
                    revision_label="-",
                    file_storage_uuid=file_info["uuid"],
                    original_filename=filename,
                    mime_type="application/pdf",
                    file_size_bytes=file_info["size_bytes"],
                    sha256_hash=file_info["sha256"],
                    is_current=True,
                    author_id=current_user.id,
                )
                db.add(revision)
                
                # Step 10: Notify responsible user and admins
                notify_item_imported(db, item, responsible_id)
                
                created_count += 1
                
            except IntegrityError as e:
                db.rollback()
                errors.append({"filename": filename, "error": f"Database error: {str(e)}"})
                # Re-raise to trigger full rollback
                raise
            except Exception as e:
                errors.append({"filename": filename, "error": str(e)})
                continue
        
        # Commit all changes atomically
        db.commit()
        
        return {
            "created_count": created_count,
            "errors": errors,
        }
        
    except Exception as e:
        # Rollback transaction
        db.rollback()
        
        # Cleanup saved files
        for file_uuid in saved_files:
            try:
                delete_file(file_uuid)
            except Exception:
                pass
        
        # Return error
        return {
            "created_count": 0,
            "errors": [{"filename": "batch", "error": f"Transaction failed: {str(e)}"}],
        }


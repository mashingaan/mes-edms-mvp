"""Script to seed demo data for demonstration purposes.

Usage:
    docker-compose exec backend python scripts/seed_demo_data.py
    
    Or locally:
    cd backend && python scripts/seed_demo_data.py
"""
import os
import sys
import io
import asyncio
from uuid import UUID
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.project_section import ProjectSection
from app.models.item import Item, ItemStatus
from app.models.progress_history import ProgressHistory
from app.utils.security import hash_password
from app.services.import_service import import_items_from_files
from app.utils.filename_parser import parse_filename
from fastapi import UploadFile
from starlette.datastructures import Headers


def seed_demo_data():
    """Seed demo data for demonstration."""
    db = SessionLocal()
    try:
        print("Starting demo data seeding...")
        
        # Get admin user for progress history
        admin = db.query(User).filter(User.role == UserRole.admin).first()
        if not admin:
            print("Error: Admin user not found. Run migrations first.")
            return
        
        # Create demo users with different roles
        demo_users = []
        
        # User 1: Responsible
        user1 = db.query(User).filter(User.email == "engineer@example.com").first()
        if not user1:
            user1 = User(
                full_name="Ivanov Ivan",
                email="engineer@example.com",
                password_hash=hash_password("engineer123"),
                role=UserRole.responsible,
                is_active=True,
            )
            db.add(user1)
            db.flush()
            print("Created user: engineer@example.com (responsible)")
        demo_users.append(user1)
        
        # User 2: Responsible
        user2 = db.query(User).filter(User.email == "designer@example.com").first()
        if not user2:
            user2 = User(
                full_name="Petrov Petr",
                email="designer@example.com",
                password_hash=hash_password("designer123"),
                role=UserRole.responsible,
                is_active=True,
            )
            db.add(user2)
            db.flush()
            print("Created user: designer@example.com (responsible)")
        demo_users.append(user2)
        
        # User 3: Viewer
        user3 = db.query(User).filter(User.email == "viewer@example.com").first()
        if not user3:
            user3 = User(
                full_name="Sidorov Sergey",
                email="viewer@example.com",
                password_hash=hash_password("viewer123"),
                role=UserRole.viewer,
                is_active=True,
            )
            db.add(user3)
            db.flush()
            print("Created user: viewer@example.com (viewer)")
        demo_users.append(user3)
        
        # Create Project 1
        project1 = db.query(Project).filter(Project.name == "Turbine Assembly A-100").first()
        if not project1:
            project1 = Project(
                name="Turbine Assembly A-100",
                description="Main turbine assembly project for Q1 2025 delivery",
                status=ProjectStatus.active,
            )
            db.add(project1)
            db.flush()
            print("Created project: Turbine Assembly A-100")
        
        # Create sections for Project 1: "БНС.КМД", "БНС.ТХ"
        section1_kmd = db.query(ProjectSection).filter(
            ProjectSection.project_id == project1.id,
            ProjectSection.code == "БНС.КМД"
        ).first()
        if not section1_kmd:
            section1_kmd = ProjectSection(
                project_id=project1.id,
                code="БНС.КМД"
            )
            db.add(section1_kmd)
            db.flush()
            print("Created section: БНС.КМД for Project 1")
        
        section1_th = db.query(ProjectSection).filter(
            ProjectSection.project_id == project1.id,
            ProjectSection.code == "БНС.ТХ"
        ).first()
        if not section1_th:
            section1_th = ProjectSection(
                project_id=project1.id,
                code="БНС.ТХ"
            )
            db.add(section1_th)
            db.flush()
            print("Created section: БНС.ТХ for Project 1")
        
        # Create Project 2
        project2 = db.query(Project).filter(Project.name == "Control Panel B-200").first()
        if not project2:
            project2 = Project(
                name="Control Panel B-200",
                description="Electronic control panel development",
                status=ProjectStatus.active,
            )
            db.add(project2)
            db.flush()
            print("Created project: Control Panel B-200")
        
        # Create sections for Project 2: "ЭЛ.ПУ", "МЕХ.СБ"
        section2_elpu = db.query(ProjectSection).filter(
            ProjectSection.project_id == project2.id,
            ProjectSection.code == "ЭЛ.ПУ"
        ).first()
        if not section2_elpu:
            section2_elpu = ProjectSection(
                project_id=project2.id,
                code="ЭЛ.ПУ"
            )
            db.add(section2_elpu)
            db.flush()
            print("Created section: ЭЛ.ПУ for Project 2")
        
        section2_mehsb = db.query(ProjectSection).filter(
            ProjectSection.project_id == project2.id,
            ProjectSection.code == "МЕХ.СБ"
        ).first()
        if not section2_mehsb:
            section2_mehsb = ProjectSection(
                project_id=project2.id,
                code="МЕХ.СБ"
            )
            db.add(section2_mehsb)
            db.flush()
            print("Created section: МЕХ.СБ for Project 2")
        
        # Import demo files using the same flow as the import endpoint
        def build_demo_upload(filename: str) -> UploadFile:
            content = (
                b"%PDF-1.4\n"
                b"% Demo PDF\n"
                b"1 0 obj\n"
                b"<<>>\n"
                b"endobj\n"
                b"trailer\n"
                b"<<>>\n"
                b"%%EOF\n"
            )
            file_obj = io.BytesIO(content)
            headers = Headers({"content-type": "application/pdf"})
            return UploadFile(file=file_obj, filename=filename, headers=headers)

        def resolve_part_number(filename: str) -> str:
            parsed = parse_filename(filename)
            part_number = parsed.get("part_number")
            if not part_number:
                base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                part_number = base_name.replace(' ', '_')[:100]
            return part_number

        def import_demo_files(project: Project, filenames, responsible_id: UUID) -> None:
            pending_files = []
            for filename in filenames:
                part_number = resolve_part_number(filename)
                existing_item = db.query(Item).filter(Item.part_number == part_number).first()
                if existing_item:
                    continue
                pending_files.append(build_demo_upload(filename))

            if not pending_files:
                print(f"No new demo files to import for {project.name}")
                return

            result = asyncio.run(
                import_items_from_files(
                    db=db,
                    project_id=project.id,
                    files=pending_files,
                    section_id=None,
                    responsible_id=responsible_id,
                    current_user=admin,
                )
            )
            if result["errors"]:
                print(f"Import errors for {project.name}: {result['errors']}")
            print(f"Imported {result['created_count']} demo items for {project.name}")

        project1_filenames = [
            "БНС.КМД.123.456.789.001 Корпус.pdf",
            "БНС.КМД.123.456.789.002 Крышка.pdf",
            "БНС.ТХ.24. Ротор сборка.pdf",
        ]

        project2_filenames = [
            "ЭЛ.ПУ.111.222.333.001 Main Board.pdf",
            "ЭЛ.ПУ.111.222.333.002 Power Supply.pdf",
            "МЕХ.СБ.45. Панель интерфейса.pdf",
        ]

        import_demo_files(project1, project1_filenames, user1.id)
        import_demo_files(project2, project2_filenames, user2.id)

        # Update progress and add history for imported items
        progress_updates = [
            {
                "part_number": "123.456.789.001",
                "status": ItemStatus.in_progress,
                "progress": 45,
                "history": [
                    (0, 15, "Initial documentation started", 5),
                    (15, 45, "Documentation in progress", 2),
                ],
            },
            {
                "part_number": "123.456.789.002",
                "status": ItemStatus.in_progress,
                "progress": 30,
                "history": [
                    (0, 30, "Initial documentation started", 4),
                ],
            },
            {
                "part_number": "24",
                "status": ItemStatus.in_progress,
                "progress": 60,
                "history": [
                    (0, 30, "Initial documentation started", 6),
                    (30, 60, "Documentation in progress", 3),
                ],
            },
            {
                "part_number": "111.222.333.001",
                "status": ItemStatus.in_progress,
                "progress": 80,
                "history": [
                    (0, 50, "First phase completed", 10),
                    (50, 80, "Documentation in progress", 4),
                ],
            },
            {
                "part_number": "111.222.333.002",
                "status": ItemStatus.completed,
                "progress": 100,
                "history": [
                    (0, 50, "First phase completed", 10),
                    (50, 100, "All documentation complete", 3),
                ],
            },
            {
                "part_number": "45",
                "status": ItemStatus.draft,
                "progress": 20,
                "history": [
                    (0, 20, "Initial documentation started", 1),
                ],
            },
        ]

        for update in progress_updates:
            item = db.query(Item).filter(Item.part_number == update["part_number"]).first()
            if not item:
                continue

            item.status = update["status"]
            item.current_progress = update["progress"]
            item.docs_completion_percent = update["progress"]

            existing_history = db.query(ProgressHistory).filter(
                ProgressHistory.item_id == item.id
            ).first()
            if existing_history:
                continue

            for old_progress, new_progress, comment, days_ago in update["history"]:
                history_entry = ProgressHistory(
                    item_id=item.id,
                    old_progress=old_progress,
                    new_progress=new_progress,
                    changed_by=admin.id,
                    changed_at=datetime.utcnow() - timedelta(days=days_ago),
                    comment=comment,
                )
                db.add(history_entry)

        print("\nSeeded import demo files:")
        for filename in project1_filenames + project2_filenames:
            print(f"  - {filename}")

        db.commit()
        print("\nDemo data seeding completed successfully!")
        print("\nDemo Users:")
        print("  - admin@example.com / adminpassword (admin)")
        print("  - engineer@example.com / engineer123 (responsible)")
        print("  - designer@example.com / designer123 (responsible)")
        print("  - viewer@example.com / viewer123 (viewer)")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()


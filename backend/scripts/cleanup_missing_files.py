"""
Script to mark tech documents as deleted when their files are missing.
"""
from datetime import datetime

from app.database import SessionLocal
from app.models.tech_document import TechDocument
from app.services.file_storage_service import get_candidate_paths


def cleanup_missing_files() -> None:
    session = SessionLocal()
    try:
        documents = (
            session.query(TechDocument)
            .filter(TechDocument.is_deleted == False)  # noqa: E712
            .all()
        )

        missing_count = 0
        for doc in documents:
            candidate_paths = get_candidate_paths(
                doc.storage_uuid,
                doc.file_extension,
                kind="tech",
            )

            found_path = next((path for path in candidate_paths if path.exists()), None)
            if found_path:
                if candidate_paths and found_path != candidate_paths[0]:
                    print(
                        "legacy path hit: found tech doc under "
                        f"{found_path.parent}, not deleting; consider migration"
                    )
                continue

            print(f"missing in all roots -> marking deleted: {doc.filename} (UUID: {doc.storage_uuid})")
            doc.is_deleted = True
            doc.deleted_at = datetime.utcnow()
            missing_count += 1

        if missing_count > 0:
            session.commit()
            print(f"\nTotal missing files marked as deleted: {missing_count}")
        else:
            print("All files exist, no cleanup needed")
    finally:
        session.close()


if __name__ == "__main__":
    cleanup_missing_files()

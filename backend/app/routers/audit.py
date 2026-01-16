from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import list_audit_logs
from app.dependencies import require_role

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse], dependencies=[Depends(require_role(["admin"]))])
def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    logs = list_audit_logs(
        db,
        page=page,
        per_page=per_page,
        user_id=user_id,
        action_type=action_type,
        start_date=start_date,
        end_date=end_date
    )
    return [AuditLogResponse.model_validate(log) for log in logs]


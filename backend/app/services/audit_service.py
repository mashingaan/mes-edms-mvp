from uuid import UUID
from typing import Optional, List, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    user_id: Optional[UUID],
    action_type: str,
    payload: dict[str, Any],
    ip_address: Optional[str] = None
) -> AuditLog:
    """Log an action to audit log."""
    log_entry = AuditLog(
        user_id=user_id,
        action_type=action_type,
        payload=payload,
        ip_address=ip_address,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def list_audit_logs(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[AuditLog]:
    """List audit logs with filtering and pagination."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    # Order by timestamp descending
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    return query.all()


from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import (
    create_user,
    get_user,
    list_users,
    update_user,
    deactivate_user,
)
from app.services.audit_service import log_action
from app.dependencies import get_current_user, require_role
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[UserResponse], dependencies=[Depends(require_role(["admin"]))])
async def get_users(db: Session = Depends(get_db)):
    users = list_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse)
async def create_new_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = create_user(db, user_data)
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="user.create",
        payload={"created_user_id": str(user.id), "email": user.email},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_role(["admin"]))])
async def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    request: Request,
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="user.update",
        payload={"updated_user_id": str(user_id), "changes": user_data.model_dump(exclude_unset=True)},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user_by_id(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Audit log
    log_action(
        db,
        user_id=current_user.id,
        action_type="user.delete",
        payload={"deleted_user_id": str(user_id)},
        ip_address=getattr(request.state, "ip", None)
    )
    
    return UserResponse.model_validate(user)


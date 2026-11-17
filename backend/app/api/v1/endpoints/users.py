from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserResponse
from app.schemas.registration import RegistrationResponse
from fastapi import HTTPException, status
from app.schemas.user import UserRoleUpdate
from app.dependencies.auth import get_current_admin
from app.services.registration_service import get_my_registrations
from sqlalchemy import select, func
from app.models.user import UserRole
from app.services.user_service import list_users, update_profile


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get(
    "/me/registrations",
    response_model=list[RegistrationResponse]
)
def list_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_my_registrations(db, current_user)


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch("/me", response_model=UserResponse)
def edit_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_profile(db, current_user, profile_data)


@router.get("/", response_model=list[UserResponse])
def list_all_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return list_users(db, skip=skip, limit=limit)

@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role == UserRole.ADMIN and role_data.role != UserRole.ADMIN:
        admin_count = db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.ADMIN)
        ) or 0
        if admin_count <= 1:
            raise HTTPException(status_code=409, detail="Cannot demote the last administrator")

    user.role = role_data.role

    db.commit()
    db.refresh(user)

    return user

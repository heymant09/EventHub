from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse
)
from app.services import category_service


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db)
):
    return category_service.get_categories(db)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.create_category(
        db, category_data, current_user
    )


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.update_category(
        db, category_id, category_data, current_user
    )


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.delete_category(
        db, category_id, current_user
    )
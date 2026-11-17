from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.category import Category
from app.models.user import User, UserRole


def check_admin(current_user: User):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage categories"
        )


def create_category(db: Session, category_data, current_user: User):
    check_admin(current_user)

    category = Category(
        name=category_data.name.strip(),
        description=category_data.description
    )

    db.add(category)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists"
        )

    return category


def get_categories(db: Session):
    statement = select(Category).order_by(Category.name.asc())
    return db.scalars(statement).all()


def update_category(
    db: Session,
    category_id: int,
    category_data,
    current_user: User
):
    check_admin(current_user)

    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    update_data = category_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip()

    for field, value in update_data.items():
        setattr(category, field, value)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists"
        )

    return category


def delete_category(
    db: Session,
    category_id: int,
    current_user: User
):
    check_admin(current_user)

    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Remove event-category associations before deleting.
    category.events.clear()

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}
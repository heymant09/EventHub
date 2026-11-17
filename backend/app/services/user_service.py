from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserProfileUpdate
from app.core.security import hash_password


class EmailAlreadyRegisteredError(Exception):
    pass


def create_user(db: Session, user_data: UserCreate) -> User:

    # 1. Check whether email already exists
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise EmailAlreadyRegisteredError(
            "This email is already registered."
        )

    # 2. Hash the password
    hashed_password = hash_password(user_data.password)

    # 3. Create SQLAlchemy User object
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password
    )

    # 4. Add user to database session
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        # Handles duplicate email attempts that happen concurrently
        raise EmailAlreadyRegisteredError(
            "This email is already registered."
        ) from exc

    # 5. Retrieve database-generated values
    db.refresh(new_user)

    return new_user

def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> User | None:

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user


def list_users(db: Session, *, skip: int = 0, limit: int = 100) -> list[User]:
    statement = select(User).order_by(User.id.asc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def update_profile(db: Session, user: User, data: UserProfileUpdate) -> User:
    changes = data.model_dump(exclude_unset=True)
    current_password = changes.pop("current_password", None)
    new_password = changes.pop("new_password", None)

    if new_password is not None and not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if "email" in changes:
        existing = db.scalar(select(User).where(User.email == changes["email"], User.id != user.id))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered")

    for field, value in changes.items():
        setattr(user, field, value)
    if new_password is not None:
        user.password_hash = hash_password(new_password)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered") from exc

    db.refresh(user)
    return user

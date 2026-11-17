import argparse
import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def create_admin() -> None:
    name = input("Administrator name: ").strip()
    email = input("Administrator email: ").strip().lower()

    password = getpass.getpass("Password (minimum 8 characters): ")
    confirm_password = getpass.getpass("Confirm password: ")

    if not name:
        raise SystemExit("Name is required.")

    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters.")

    if password != confirm_password:
        raise SystemExit("Passwords do not match.")

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User.id).where(User.role == UserRole.ADMIN).limit(1)
        )

        if existing_admin is not None:
            raise SystemExit("An administrator already exists; bootstrap refused.")

        existing_user = db.scalar(
            select(User.id).where(User.email == email)
        )

        if existing_user is not None:
            raise SystemExit("That email is already registered.")

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN
        )

        db.add(admin)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise SystemExit("Could not create administrator. Check whether the email already exists.")

    print("Administrator created successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("command", choices=["create-admin"])

    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin()


if __name__ == "__main__":
    main()
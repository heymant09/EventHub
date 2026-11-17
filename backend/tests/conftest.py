import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
# Import all models so Base knows about tables
import app.models


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    Base.metadata.create_all(bind=eng)

    try:
        yield eng
    finally:
        Base.metadata.drop_all(bind=eng)
        eng.dispose()


@pytest.fixture
def TestingSessionLocal(engine):
    """Session factory bound to the test engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(TestingSessionLocal):
    """Provide a DB session for direct DB operations."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def organiser_token(client, db_session):
    """Create an organiser and return their JWT."""

    from app.models.user import User, UserRole

    organiser_data = {
        "name": "Organiser User",
        "email": "organiser@example.com",
        "password": "StrongPass123!",
    }

    # Register through the public API.
    response = client.post(
        "/api/v1/auth/register",
        json=organiser_data,
    )
    assert response.status_code == 201, response.text

    # Promote the user for testing.
    organiser = db_session.query(User).filter(
        User.email == organiser_data["email"]
    ).first()

    assert organiser is not None

    organiser.role = UserRole.ORGANISER
    db_session.commit()

    # Login after promotion.
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": organiser_data["email"],
            "password": organiser_data["password"],
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]

@pytest.fixture
def second_organiser_token(client, db_session):
    from app.models.user import User, UserRole

    user_data = {
        "name": "Second Organiser",
        "email": "secondorganiser@example.com",
        "password": "StrongPass123!",
    }

    # Register through the API
    response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201, response.text

    # Promote using the isolated test database
    organiser = db_session.query(User).filter(
        User.email == user_data["email"]
    ).first()

    assert organiser is not None

    organiser.role = UserRole.ORGANISER
    db_session.commit()

    # Login after promotion
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert response.status_code == 200, response.text

    return response.json()["access_token"]

@pytest.fixture
def client(TestingSessionLocal):
    """FastAPI TestClient using the isolated test database."""

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(fastapi_app) as test_client:
            yield test_client
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def admin_token(client, db_session):
    """Create an admin user and return its JWT."""

    from app.models.user import UserRole
    from app.schemas.user import UserCreate
    from app.services.user_service import create_user

    admin_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "StrongPass123!",
    }

    # Create the user directly through the service.
    admin = create_user(db_session, UserCreate(**admin_data))

    # Promote the user to ADMIN.
    admin.role = UserRole.ADMIN
    db_session.commit()

    # Login directly; don't register the user again.
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_data["email"],
            "password": admin_data["password"],
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]

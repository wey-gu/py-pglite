"""
Advanced FastAPI Authentication Example with py-pglite

This example demonstrates production-ready patterns for testing FastAPI applications
with authentication, user roles, and complex relationships using py-pglite.

Key patterns shown:
1. JWT Authentication with superuser creation
2. Role-based access control
3. Complex model relationships
4. Function-scoped test isolation
5. Environment-based configuration
6. Realistic API endpoints with authentication
7. Proper cleanup and fixture composition
"""

import logging
from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi.testclient import TestClient
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, delete, select

# Configuration
SECRET_KEY = "test-secret-key-for-pytest"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
security = HTTPBearer()

# Logging setup
logger = logging.getLogger(__name__)


# Models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    is_superuser: bool = False


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_superuser: bool


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int


class Token(BaseModel):
    access_token: str
    token_type: str


class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str | None = None
    is_superuser: bool = False
    is_active: bool = True


class Project(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    owner_id: int = Field(foreign_key="user.id")


# Authentication utilities
def verify_password(hashed_password: str, plain_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# CRUD operations
def create_user(session: Session, user_create: UserCreate) -> User:
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        full_name=user_create.full_name,
        is_superuser=user_create.is_superuser,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session, email)
    if not user or not verify_password(
        hashed_password=user.hashed_password,
        plain_password=password,
    ):
        return None
    return user


# FastAPI App
def create_app() -> FastAPI:
    app = FastAPI(title="Advanced Auth Example")

    # Database dependency (will be overridden in tests)
    def get_db():
        raise NotImplementedError("Database dependency should be overridden in tests")

    # Authentication dependency
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db),
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
            )
            email = payload.get("sub")
            if not isinstance(email, str) or email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = get_user_by_email(db, email)
        if user is None:
            raise credentials_exception
        return user

    def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    # Routes
    @app.post("/auth/login", response_model=Token)
    def login(email: str, password: str, db: Session = Depends(get_db)):
        user = authenticate_user(db, email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    @app.post("/users/", response_model=UserRead)
    def create_user_endpoint(
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_superuser),
    ):
        db_user = get_user_by_email(db, user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        return create_user(db, user)

    @app.get("/users/me", response_model=UserRead)
    def read_users_me(current_user: User = Depends(get_current_user)):
        return current_user

    @app.get("/users/", response_model=list[UserRead])
    def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_superuser),
    ):
        users = db.exec(statement=select(User).offset(skip).limit(limit)).all()
        return users

    @app.post("/projects/", response_model=ProjectRead)
    def create_project(
        project: ProjectCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        db_project = Project(
            name=project.name,
            description=project.description,
            owner_id=current_user.id
            if current_user.id is not None
            else 0,  # Ensure owner_id is int
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @app.get("/projects/", response_model=list[ProjectRead])
    def read_projects(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        projects = db.exec(select(Project).offset(skip).limit(limit)).all()
        return projects

    @app.get("/projects/{project_id}", response_model=ProjectRead)
    def read_project(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        project = db.exec(select(Project).where(Project.id == project_id)).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    # Store dependencies for testing
    app.state.get_db = get_db
    app.state.get_current_user = get_current_user
    app.state.get_current_superuser = get_current_superuser

    return app


# Test Fixtures
@pytest.fixture(scope="function")
def clean_db(pglite_session: Session) -> Generator[Session, None, None]:
    """Create a clean database session for each test."""
    # Create tables if they don't exist
    SQLModel.metadata.create_all(bind=pglite_session.get_bind())
    yield pglite_session
    # Clean up after test
    for table in reversed(SQLModel.metadata.sorted_tables):
        pglite_session.execute(delete(table))
    pglite_session.commit()


@pytest.fixture(scope="function")
def app_with_db(clean_db: Session) -> Generator[FastAPI, None, None]:
    """Create FastAPI app with database dependency override."""
    app = create_app()

    def override_get_db():
        try:
            yield clean_db
        finally:
            pass

    # Override the database dependency
    app.dependency_overrides[app.state.get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app_with_db: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app_with_db)


@pytest.fixture(scope="function")
def superuser(clean_db: Session) -> User:
    """Create a superuser for testing."""
    user_create = UserCreate(
        email="admin@example.com",
        password="test-password",
        full_name="Test Admin",
        is_superuser=True,
    )
    return create_user(clean_db, user_create)


@pytest.fixture(scope="function")
def normal_user(clean_db: Session) -> User:
    """Create a normal user for testing."""
    user_create = UserCreate(
        email="user@example.com",
        password="test-password",
        full_name="Test User",
        is_superuser=False,
    )
    return create_user(clean_db, user_create)


@pytest.fixture(scope="function")
def superuser_token(client: TestClient, superuser: User) -> str:
    """Get superuser authentication token."""
    response = client.post(
        "/auth/login", params={"email": superuser.email, "password": "test-password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def normal_user_token(client: TestClient, normal_user: User) -> str:
    """Get normal user authentication token."""
    response = client.post(
        "/auth/login", params={"email": normal_user.email, "password": "test-password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def superuser_headers(superuser_token: str) -> dict[str, str]:
    """Get superuser authorization headers."""
    return {"Authorization": f"Bearer {superuser_token}"}


@pytest.fixture(scope="function")
def normal_user_headers(normal_user_token: str) -> dict[str, str]:
    """Get normal user authorization headers."""
    return {"Authorization": f"Bearer {normal_user_token}"}


# Tests
def test_create_superuser(clean_db: Session):
    """Test superuser creation and authentication."""
    user_create = UserCreate(
        email="admin@example.com", password="secret123", is_superuser=True
    )

    user = create_user(clean_db, user_create)

    assert user.email == "admin@example.com"
    assert user.is_superuser is True
    assert verify_password(user.hashed_password, "secret123")


def test_user_authentication(client: TestClient, superuser: User):
    """Test user login and token generation."""
    # Test successful login
    response = client.post(
        "/auth/login", params={"email": superuser.email, "password": "test-password"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test failed login
    response = client.post(
        "/auth/login", params={"email": superuser.email, "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_get_current_user(client: TestClient, superuser: User, superuser_headers: dict):
    """Test getting current user information."""
    response = client.get("/users/me", headers=superuser_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == superuser.email
    assert data["is_superuser"] is True


def test_unauthorized_access(client: TestClient):
    """Test accessing protected endpoints without authentication."""
    response = client.get("/users/me")
    assert response.status_code == 403  # FastAPI returns 403 for missing auth


def test_create_user_as_superuser(client: TestClient, superuser_headers: dict):
    """Test creating users with superuser privileges."""
    user_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User",
    }

    response = client.post("/users/", json=user_data, headers=superuser_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["is_superuser"] is False


def test_create_user_as_normal_user(client: TestClient, normal_user_headers: dict):
    """Test that normal users cannot create other users."""
    user_data = {"email": "newuser@example.com", "password": "password123"}

    response = client.post("/users/", json=user_data, headers=normal_user_headers)

    assert response.status_code == 403


def test_list_users_permissions(
    client: TestClient, superuser_headers: dict, normal_user_headers: dict
):
    """Test user listing permissions."""
    # Superuser can list users
    response = client.get("/users/", headers=superuser_headers)
    assert response.status_code == 200

    # Normal user cannot list users
    response = client.get("/users/", headers=normal_user_headers)
    assert response.status_code == 403


def test_project_crud(client: TestClient, normal_user: User, normal_user_headers: dict):
    """Test project creation and management."""
    # Create project
    project_data = {"name": "Test Project", "description": "A test project"}

    response = client.post("/projects/", json=project_data, headers=normal_user_headers)

    assert response.status_code == 200
    project = response.json()
    assert project["name"] == "Test Project"
    assert project["owner_id"] == normal_user.id

    # List projects
    response = client.get("/projects/", headers=normal_user_headers)
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 1

    # Get specific project
    project_id = project["id"]
    response = client.get(f"/projects/{project_id}", headers=normal_user_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_project_unauthorized(client: TestClient):
    """Test project endpoints require authentication."""
    project_data = {"name": "Test Project"}

    response = client.post("/projects/", json=project_data)
    assert response.status_code == 403

    response = client.get("/projects/")
    assert response.status_code == 403


def test_duplicate_email(client: TestClient, superuser: User, superuser_headers: dict):
    """Test creating user with duplicate email."""
    user_data = {
        "email": superuser.email,  # Use existing email
        "password": "password123",
    }

    response = client.post("/users/", json=user_data, headers=superuser_headers)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_complex_scenario(
    client: TestClient, clean_db: Session, superuser: User, superuser_headers: dict
):
    """Test complex scenario with multiple users and projects."""
    # Create additional users
    users_data = [
        {"email": "alice@example.com", "password": "pass123", "full_name": "Alice"},
        {"email": "bob@example.com", "password": "pass123", "full_name": "Bob"},
    ]

    created_users = []
    for user_data in users_data:
        response = client.post("/users/", json=user_data, headers=superuser_headers)
        assert response.status_code == 200
        created_users.append(response.json())

    # Login as Alice and create project
    alice_token_response = client.post(
        "/auth/login", params={"email": "alice@example.com", "password": "pass123"}
    )
    alice_headers = {
        "Authorization": f"Bearer {alice_token_response.json()['access_token']}"
    }

    project_response = client.post(
        "/projects/",
        json={"name": "Alice's Project", "description": "Alice's first project"},
        headers=alice_headers,
    )
    assert project_response.status_code == 200

    # Verify superuser can see all users and projects
    users_response = client.get("/users/", headers=superuser_headers)
    all_users = users_response.json()
    assert len(all_users) >= 3  # superuser + alice + bob

    projects_response = client.get("/projects/", headers=alice_headers)
    all_projects = projects_response.json()
    assert len(all_projects) >= 1


def test_token_expiration_simulation(client: TestClient, superuser: User):
    """Test behavior with expired tokens (simulated)."""
    # Create a token with very short expiration
    short_token = create_access_token(
        data={"sub": superuser.email},
        expires_delta=timedelta(seconds=-1),  # Already expired
    )

    headers = {"Authorization": f"Bearer {short_token}"}
    response = client.get("/users/me", headers=headers)

    # Should fail with 401 due to expired token
    assert response.status_code == 401


if __name__ == "__main__":
    # Example of running specific test
    pytest.main([__file__ + "::test_complex_scenario", "-v"])

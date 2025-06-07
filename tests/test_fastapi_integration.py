"""Example showing how to integrate py-pglite with FastAPI testing."""

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Field, Session, SQLModel, create_engine, select

from py_pglite.sqlalchemy import pglite_engine


# Example models
class UserCreate(SQLModel):
    name: str
    email: str


class APIUser(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str


class UserRead(SQLModel):
    id: int
    name: str
    email: str


# FastAPI app
app = FastAPI()

# Database dependency (will be overridden in tests)
def get_db():
    # This would normally connect to your production database
    raise NotImplementedError("Database dependency should be overridden in tests")


@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = APIUser(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.exec(select(APIUser).where(APIUser.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    users = db.exec(select(APIUser)).all()
    return users


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.exec(select(APIUser).where(APIUser.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


# Test fixtures
@pytest.fixture(scope="module")
def test_app(pglite_engine):
    """Create FastAPI test app with PGlite database."""
    # Create tables
    SQLModel.metadata.create_all(pglite_engine)

    # Override database dependency
    def override_get_db():
        with Session(pglite_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield app

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


# Tests
def test_create_user(client: TestClient):
    """Test creating a user via API."""
    response = client.post(
        "/users/",
        json={"name": "Alice", "email": "alice@example.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_get_user(client: TestClient):
    """Test getting a user via API."""
    # First create a user
    create_response = client.post(
        "/users/",
        json={"name": "Bob", "email": "bob@example.com"}
    )
    user_id = create_response.json()["id"]

    # Then get the user
    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "Bob"
    assert data["email"] == "bob@example.com"


def test_get_nonexistent_user(client: TestClient):
    """Test getting a user that doesn't exist."""
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_list_users(client: TestClient):
    """Test listing all users."""
    # Create some users
    users_data = [
        {"name": "Charlie", "email": "charlie@example.com"},
        {"name": "Diana", "email": "diana@example.com"},
    ]

    created_users = []
    for user_data in users_data:
        response = client.post("/users/", json=user_data)
        created_users.append(response.json())

    # List all users
    response = client.get("/users/")

    assert response.status_code == 200
    users = response.json()

    # Should include our created users (plus any from previous tests)
    assert len(users) >= 2

    # Check our created users are in the list
    user_names = {user["name"] for user in users}
    assert "Charlie" in user_names
    assert "Diana" in user_names


def test_delete_user(client: TestClient):
    """Test deleting a user."""
    # First create a user
    create_response = client.post(
        "/users/",
        json={"name": "Eve", "email": "eve@example.com"}
    )
    user_id = create_response.json()["id"]

    # Delete the user
    delete_response = client.delete(f"/users/{user_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted"

    # Verify user is gone
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_user(client: TestClient):
    """Test deleting a user that doesn't exist."""
    response = client.delete("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_email_uniqueness_constraint(client: TestClient):
    """Test that we can handle database constraints."""
    # Create first user
    response1 = client.post(
        "/users/",
        json={"name": "Frank", "email": "frank@example.com"}
    )
    assert response1.status_code == 200

    # Try to create another user with same email
    # Note: This test assumes no unique constraint on email in the model
    # If you add a unique constraint, this test would need to expect a 400/422 error
    response2 = client.post(
        "/users/",
        json={"name": "Frank Jr", "email": "frank@example.com"}
    )

    # Without unique constraint, this should succeed
    assert response2.status_code == 200

    # Both users should exist
    users = client.get("/users/").json()
    frank_users = [u for u in users if u["email"] == "frank@example.com"]
    assert len(frank_users) == 2


# Example of testing with manual database setup
def test_with_manual_db_setup(pglite_engine):
    """Test using PGlite engine directly for more control."""
    # Create tables
    SQLModel.metadata.create_all(pglite_engine)

    # Create app with custom dependency
    test_app = FastAPI()

    @test_app.post("/users/", response_model=UserRead)
    def create_user_endpoint(user: UserCreate):
        with Session(pglite_engine) as db:
            db_user = APIUser(name=user.name, email=user.email)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user

    # Test the endpoint
    with TestClient(test_app) as client:
        response = client.post(
            "/users/",
            json={"name": "Grace", "email": "grace@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Grace"
        assert data["email"] == "grace@example.com"

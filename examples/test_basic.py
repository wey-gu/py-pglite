"""Basic example showing how to use py-pglite fixtures."""

from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import select


# Example model
class BasicUser(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str


def test_user_creation(pglite_session: Session):
    """Test creating and querying users."""
    # Create a user
    user = BasicUser(name="Alice", email="alice@example.com")
    pglite_session.add(user)
    pglite_session.commit()

    # Query it back
    users = pglite_session.exec(select(BasicUser)).all()
    assert len(users) == 1
    assert users[0].name == "Alice"
    assert users[0].email == "alice@example.com"


def test_multiple_users(pglite_session: Session):
    """Test creating multiple users."""
    # Create multiple users
    users = [
        BasicUser(name="Bob", email="bob@example.com"),
        BasicUser(name="Charlie", email="charlie@example.com"),
    ]

    for user in users:
        pglite_session.add(user)
    pglite_session.commit()

    # Query all users
    all_users = pglite_session.exec(select(BasicUser)).all()
    assert len(all_users) == 2

    # Query by name
    bob = pglite_session.exec(select(BasicUser).where(BasicUser.name == "Bob")).first()
    assert bob is not None
    assert bob.email == "bob@example.com"


def test_user_update(pglite_session: Session):
    """Test updating a user."""
    # Create a user
    user = BasicUser(name="David", email="david@old.com")
    pglite_session.add(user)
    pglite_session.commit()

    # Update the email
    user.email = "david@new.com"
    pglite_session.add(user)
    pglite_session.commit()

    # Verify the update
    updated_user = pglite_session.exec(
        select(BasicUser).where(BasicUser.name == "David")
    ).first()
    assert updated_user is not None
    assert updated_user.email == "david@new.com"


def test_user_deletion(pglite_session: Session):
    """Test deleting a user."""
    # Create a user
    user = BasicUser(name="Eve", email="eve@example.com")
    pglite_session.add(user)
    pglite_session.commit()

    # Delete the user
    pglite_session.delete(user)
    pglite_session.commit()

    # Verify deletion
    users = pglite_session.exec(select(BasicUser)).all()
    assert len(users) == 0

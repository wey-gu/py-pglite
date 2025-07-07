#!/usr/bin/env python3
"""
🚀 Instant FastAPI + PostgreSQL
==============================

Zero-config FastAPI app with real PostgreSQL in 30 seconds.

Usage:
    pip install fastapi uvicorn sqlalchemy
    python simple_fastapi.py
    # Open http://localhost:8000/docs
"""

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


# ⚡ ONE LINE SETUP - Real PostgreSQL ready!
manager = SQLAlchemyPGliteManager()
manager.start()
engine = manager.get_engine()

# 📊 Simple Model
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))


Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


# 🌐 Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


# 🚀 FastAPI App
app = FastAPI(
    title="⚡ py-pglite FastAPI Demo",
    description="Instant PostgreSQL API - zero config!",
    version="1.0.0",
)


@app.get("/")
def read_root():
    return {
        "message": "🚀 py-pglite + FastAPI = Instant PostgreSQL API!",
        "docs": "Visit /docs for interactive API documentation",
        "database": "Real PostgreSQL (not SQLite!)",
    }


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    """Create a new user - stored in real PostgreSQL!"""
    with SessionLocal() as db:
        db_user = User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserResponse(id=db_user.id, name=db_user.name, email=db_user.email)  # type: ignore


@app.get("/users/", response_model=list[UserResponse])
def list_users():
    """List all users from PostgreSQL."""
    with SessionLocal() as db:
        users = db.query(User).all()
        return [UserResponse(id=u.id, name=u.name, email=u.email) for u in users]  # type: ignore


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """Get a specific user by ID."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(id=user.id, name=user.name, email=user.email)  # type: ignore


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    finally:
        manager.stop()

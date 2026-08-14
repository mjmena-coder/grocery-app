# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1. Import Base AND models to register all SQLAlchemy tables
from backend.database import Base, get_session
import backend.models  # Guarantees Recipe, Ingredient, CanonicalIngredient, Store are registered

from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(name="session")
def session_fixture():
    # 2. StaticPool keeps the in-memory SQLite connection alive across all requests
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_session():
        try:
            yield session
        finally:
            pass

    # 3. Override get_session directly
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
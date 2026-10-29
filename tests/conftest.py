import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app
from scripts.seed_database import seed


@pytest.fixture
def db():
    url = os.getenv("TEST_DATABASE_URL", "sqlite://")
    options = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
    engine = create_engine(url, **(options if url == "sqlite://" else {}))
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: Settings(agent_mode="demo")
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

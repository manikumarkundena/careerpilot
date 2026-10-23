import os
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.security import hash_password
from app.db.database import get_db
from app.main import app
from app.models.user import User


TEST_DATABASE_URL = (
    "postgresql+asyncpg://careerpilot:"
    "careerpilot_dev_password@localhost:5432/careerpilot_test"
)

TEST_PASSWORD = "TestPassword123!"


@pytest.fixture(scope="session", autouse=True)
def migrate_test_database():
    """Apply all Alembic migrations to the dedicated test database before tests.

    Alembic reads DATABASE_URL from the environment, while test sessions use
    TEST_DATABASE_URL directly. Temporarily point Alembic at the test database
    so schema changes never accidentally target the development database.
    """
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    try:
        alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(alembic_config, "head")
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url


@pytest_asyncio.fixture
async def session():
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        await session.execute(
            text("TRUNCATE TABLE semantic_embeddings, jobs CASCADE")
        )
        await session.commit()

        yield session

        await session.rollback()

    await test_engine.dispose()


@pytest.fixture
def override_get_db(session):
    async def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db

    yield

    app.dependency_overrides.clear()


def create_test_user(**kwargs) -> User:
    return User(
        password_hash=hash_password(TEST_PASSWORD),
        **kwargs,
    )

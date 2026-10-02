import pytest
import pytest_asyncio

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
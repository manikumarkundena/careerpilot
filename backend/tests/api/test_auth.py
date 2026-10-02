import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.database import get_db
from app.main import app
from app.models.career_profile import CareerProfile
from app.models.user import User


def make_client():
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_register_creates_user_profile_and_token(
    session,
    override_get_db,
):
    email = f"register-{uuid.uuid4()}@example.com"

    async with make_client() as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "display_name": "Test User",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["display_name"] == "Test User"

    result = await session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one()

    assert user.password_hash != "TestPassword123!"
    assert user.password_hash

    profile_result = await session.execute(
        select(CareerProfile).where(
            CareerProfile.user_id == user.id
        )
    )
    profile = profile_result.scalar_one_or_none()

    assert profile is not None


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(
    session,
    override_get_db,
):
    email = f"duplicate-{uuid.uuid4()}@example.com"

    async with make_client() as client:
        first = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )

        second = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "AnotherPassword123!",
            },
        )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Email already registered"
    )


@pytest.mark.asyncio
async def test_login_accepts_valid_credentials(
    session,
    override_get_db,
):
    email = f"login-{uuid.uuid4()}@example.com"
    password = "TestPassword123!"

    async with make_client() as client:
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]
    assert login_response.json()["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(
    session,
    override_get_db,
):
    email = f"wrong-password-{uuid.uuid4()}@example.com"

    async with make_client() as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123!",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid email or password"
    )


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(
    session,
    override_get_db,
):
    email = f"me-{uuid.uuid4()}@example.com"

    async with make_client() as client:
        login_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )

        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

    assert response.status_code == 200
    assert response.json()["email"] == email


@pytest.mark.asyncio
async def test_me_requires_authentication(
    session,
    override_get_db,
):
    async with make_client() as client:
        response = await client.get(
            "/api/v1/auth/me"
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Authentication required"
    )


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(
    session,
    override_get_db,
):
    async with make_client() as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": "Bearer invalid-token"
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired access token"
    )

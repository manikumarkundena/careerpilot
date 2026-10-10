import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "display_name": "Application Test",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _create_job(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/jobs",
        json={
            "source": "test",
            "external_id": "application-test-job",
            "title": "Backend Engineer Intern",
            "company": "CareerPilot Test",
            "description": "Build APIs with Python.",
            "application_url": "https://example.com/jobs/backend-intern",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_list_filter_and_update_application(override_get_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        token = await _register(client, "application-owner@example.com")
        job_id = await _create_job(client)
        headers = {"Authorization": f"Bearer {token}"}

        create = await client.post(
            "/api/v1/applications",
            headers=headers,
            json={"job_id": job_id, "notes": "Review role requirements"},
        )
        assert create.status_code == 201
        created = create.json()
        assert created["status"] == "saved"
        assert created["job_title"] == "Backend Engineer Intern"
        assert created["applied_at"] is None

        duplicate = await client.post(
            "/api/v1/applications",
            headers=headers,
            json={"job_id": job_id},
        )
        assert duplicate.status_code == 409

        update = await client.patch(
            f"/api/v1/applications/{created['id']}",
            headers=headers,
            json={"status": "applied", "notes": "Submitted application"},
        )
        assert update.status_code == 200
        assert update.json()["status"] == "applied"
        assert update.json()["notes"] == "Submitted application"
        assert update.json()["applied_at"] is not None

        listed = await client.get(
            "/api/v1/applications",
            headers=headers,
            params={"status": "applied", "page": 1, "limit": 10},
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["id"] == created["id"]

        empty_filter = await client.get(
            "/api/v1/applications",
            headers=headers,
            params={"status": "offer"},
        )
        assert empty_filter.status_code == 200
        assert empty_filter.json()["total"] == 0


@pytest.mark.asyncio
async def test_application_endpoints_require_authentication(override_get_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/applications")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_application_is_not_visible_to_another_user(override_get_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        owner_token = await _register(client, "application-owner2@example.com")
        other_token = await _register(client, "application-other@example.com")
        job_id = await _create_job(client)

        create = await client.post(
            "/api/v1/applications",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"job_id": job_id},
        )
        assert create.status_code == 201
        application_id = create.json()["id"]

        response = await client.get(
            f"/api/v1/applications/{application_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == 404

        update = await client.patch(
            f"/api/v1/applications/{application_id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"status": "offer"},
        )
        assert update.status_code == 404


@pytest.mark.asyncio
async def test_create_application_rejects_missing_job(override_get_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        token = await _register(client, "application-missing-job@example.com")
        response = await client.post(
            "/api/v1/applications",
            headers={"Authorization": f"Bearer {token}"},
            json={"job_id": "00000000-0000-0000-0000-000000000001"},
        )
    assert response.status_code == 404

import pytest

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ingest_jobs_creates_new_job(
    override_get_db,
):
    payload = {
        "source": "manual",
        "jobs": [
            {
                "external_id": "api-test-001",
                "title": "Software Engineer Intern",
                "company": "CareerPilot Test",
                "description": (
                    "Build backend services using "
                    "Python and FastAPI."
                ),
                "location": "Bangalore",
                "employment_type": "Internship",
                "experience_level": "Entry Level",
                "application_url": (
                    "https://example.com/jobs/api-test-001"
                ),
            }
        ],
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/jobs/ingest",
            json=payload,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "manual"
    assert data["fetched"] == 1
    assert data["created"] == 1
    assert data["updated"] == 0


@pytest.mark.asyncio
async def test_ingest_jobs_deduplicates_existing_job(
    override_get_db,
):
    payload = {
        "source": "manual",
        "jobs": [
            {
                "external_id": "api-test-002",
                "title": "Backend Engineer Intern",
                "company": "CareerPilot Test",
                "description": "Build APIs using Python.",
                "location": "Remote",
                "application_url": (
                    "https://example.com/jobs/api-test-002"
                ),
            }
        ],
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        first_response = await client.post(
            "/api/v1/jobs/ingest",
            json=payload,
        )

        second_response = await client.post(
            "/api/v1/jobs/ingest",
            json=payload,
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["created"] == 1
    assert first_data["updated"] == 0

    assert second_data["created"] == 0
    assert second_data["updated"] == 1


@pytest.mark.asyncio
async def test_ingest_jobs_rejects_empty_jobs(
    override_get_db,
):
    payload = {
        "source": "manual",
        "jobs": [],
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/jobs/ingest",
            json=payload,
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_jobs_rejects_unknown_source(
    override_get_db,
):
    payload = {
        "source": "unknown-source",
        "jobs": [
            {
                "external_id": "api-test-003",
                "title": "Software Engineer",
                "company": "CareerPilot Test",
                "description": "Build software.",
            }
        ],
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/jobs/ingest",
            json=payload,
        )

    assert response.status_code == 404
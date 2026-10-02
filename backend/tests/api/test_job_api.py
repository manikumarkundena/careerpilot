import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_jobs(override_get_db):
    payload = {
        "source": "test_source",
        "external_id": "list-001",
        "title": "Backend Engineer Intern",
        "company": "CareerPilot Test",
        "description": "Build APIs using Python.",
        "location": "Bangalore",
        "employment_type": "Internship",
        "experience_level": "Entry Level",
        "application_url": "https://example.com/jobs/list-001",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/jobs",
            json=payload,
        )

        assert create_response.status_code == 201

        response = await client.get(
            "/api/v1/jobs",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Backend Engineer Intern"


@pytest.mark.asyncio
async def test_list_jobs_filters_by_source(
    override_get_db,
):
    jobs = [
        {
            "source": "adzuna",
            "external_id": "source-001",
            "title": "Software Engineer",
            "company": "ABB",
            "description": "Build software.",
        },
        {
            "source": "manual",
            "external_id": "source-002",
            "title": "Android Developer",
            "company": "CareerPilot",
            "description": "Build Android apps.",
        },
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for job in jobs:
            response = await client.post(
                "/api/v1/jobs",
                json=job,
            )
            assert response.status_code == 201

        response = await client.get(
            "/api/v1/jobs",
            params={"source": "adzuna"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["source"] == "adzuna"


@pytest.mark.asyncio
async def test_list_jobs_filters_by_location(
    override_get_db,
):
    jobs = [
        {
            "source": "test",
            "external_id": "location-001",
            "title": "Software Engineer",
            "company": "Company A",
            "description": "Build software.",
            "location": "Bangalore",
        },
        {
            "source": "test",
            "external_id": "location-002",
            "title": "Software Engineer",
            "company": "Company B",
            "description": "Build software.",
            "location": "Hyderabad",
        },
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for job in jobs:
            response = await client.post(
                "/api/v1/jobs",
                json=job,
            )
            assert response.status_code == 201

        response = await client.get(
            "/api/v1/jobs",
            params={"location": "bangalore"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["location"] == "Bangalore"


@pytest.mark.asyncio
async def test_list_jobs_searches_title_and_company(
    override_get_db,
):
    jobs = [
        {
            "source": "test",
            "external_id": "search-001",
            "title": "Machine Learning Engineer",
            "company": "Example AI",
            "description": "Build ML systems.",
        },
        {
            "source": "test",
            "external_id": "search-002",
            "title": "Frontend Developer",
            "company": "Web Corp",
            "description": "Build web applications.",
        },
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for job in jobs:
            response = await client.post(
                "/api/v1/jobs",
                json=job,
            )
            assert response.status_code == 201

        response = await client.get(
            "/api/v1/jobs",
            params={"search": "Machine Learning"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert (
        data["items"][0]["title"]
        == "Machine Learning Engineer"
    )


@pytest.mark.asyncio
async def test_list_jobs_pagination(
    override_get_db,
):
    for index in range(5):
        payload = {
            "source": "test",
            "external_id": f"page-{index}",
            "title": f"Engineer {index}",
            "company": "CareerPilot",
            "description": "Build software.",
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/jobs",
                json=payload,
            )

            assert response.status_code == 201

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/jobs",
            params={
                "page": 2,
                "limit": 2,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.job_discovery.service import JobDiscoveryService
from app.services.job_ingestion.adapters.base import RawJob


class FakeDiscoveryService:
    async def discover(
        self,
        session,
        *,
        source,
        query,
        location,
        page,
        limit,
    ):
        assert source == "adzuna"
        assert query == "software engineer"
        assert location == "Bangalore"
        assert page == 1
        assert limit == 2

        return {
            "fetched": 2,
            "created": 2,
            "updated": 0,
        }


@pytest.mark.asyncio
async def test_discover_jobs():
    async def override_service():
        return FakeDiscoveryService()

    from app.api.routes.job_discovery import (
        get_discovery_service,
    )

    app.dependency_overrides[
        get_discovery_service
    ] = override_service

    try:
        payload = {
            "source": "adzuna",
            "query": "software engineer",
            "location": "Bangalore",
            "page": 1,
            "limit": 2,
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/jobs/discover",
                json=payload,
            )

        assert response.status_code == 200

        data = response.json()

        assert data["source"] == "adzuna"
        assert data["query"] == "software engineer"
        assert data["location"] == "Bangalore"
        assert data["fetched"] == 2
        assert data["created"] == 2
        assert data["updated"] == 0

    finally:
        app.dependency_overrides.clear()

import httpx
import pytest

from app.services.job_ingestion.adapters.adzuna import (
    AdzunaAdapter,
)


class MockResponse:
    def __init__(
        self,
        data: dict,
        status_code: int = 200,
    ) -> None:
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "Request failed",
                request=httpx.Request(
                    "GET",
                    "https://api.adzuna.com",
                ),
                response=httpx.Response(
                    self.status_code,
                ),
            )

    def json(self) -> dict:
        return self._data


class MockAsyncClient:
    def __init__(
        self,
        response: MockResponse,
    ) -> None:
        self.response = response
        self.request_url = None
        self.request_params = None

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    async def get(
        self,
        url,
        params=None,
    ):
        self.request_url = url
        self.request_params = params
        return self.response


@pytest.mark.asyncio
async def test_adzuna_adapter_metadata():
    adapter = AdzunaAdapter(
        country="in",
        what="software engineer",
        where="Bangalore",
    )

    assert adapter.source_name == "adzuna"
    assert adapter.country == "in"
    assert adapter.what == "software engineer"
    assert adapter.where == "Bangalore"


@pytest.mark.asyncio
async def test_adzuna_adapter_maps_jobs(
    monkeypatch,
):
    response_data = {
        "results": [
            {
                "id": 12345,
                "title": "Software Engineer Intern",
                "description": (
                    "Build backend services using Python "
                    "and FastAPI."
                ),
                "created": "2026-09-22T10:30:00Z",
                "redirect_url": (
                    "https://example.com/jobs/12345"
                ),
                "contract_type": "internship",
                "contract_time": "full_time",
                "company": {
                    "display_name": "Example Corp",
                },
                "location": {
                    "display_name": "Bangalore",
                },
            }
        ]
    }

    mock_client = MockAsyncClient(
        MockResponse(response_data)
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.httpx.AsyncClient",
        lambda timeout: mock_client,
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_id",
        "test-app-id",
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_key",
        "test-app-key",
    )

    adapter = AdzunaAdapter(
        country="in",
        what="software engineer",
        where="Bangalore",
    )

    jobs = await adapter.fetch_jobs()

    assert len(jobs) == 1

    job = jobs[0]

    assert job.source == "adzuna"
    assert job.external_id == "12345"
    assert job.title == "Software Engineer Intern"
    assert job.company == "Example Corp"
    assert job.description == (
        "Build backend services using Python "
        "and FastAPI."
    )
    assert job.location == "Bangalore"
    assert job.employment_type == "internship"
    assert job.experience_level is None
    assert job.application_url == (
        "https://example.com/jobs/12345"
    )

    assert mock_client.request_params["app_id"] == (
        "test-app-id"
    )
    assert mock_client.request_params["app_key"] == (
        "test-app-key"
    )
    assert mock_client.request_params["what"] == (
        "software engineer"
    )
    assert mock_client.request_params["where"] == (
        "Bangalore"
    )


@pytest.mark.asyncio
async def test_adzuna_adapter_returns_empty_results(
    monkeypatch,
):
    mock_client = MockAsyncClient(
        MockResponse({"results": []})
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.httpx.AsyncClient",
        lambda timeout: mock_client,
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_id",
        "test-app-id",
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_key",
        "test-app-key",
    )

    adapter = AdzunaAdapter()

    jobs = await adapter.fetch_jobs()

    assert jobs == []


@pytest.mark.asyncio
async def test_adzuna_adapter_requires_credentials(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_id",
        None,
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_key",
        None,
    )

    adapter = AdzunaAdapter()

    with pytest.raises(
        RuntimeError,
        match="ADZUNA_APP_ID is not configured",
    ):
        await adapter.fetch_jobs()


@pytest.mark.asyncio
async def test_adzuna_adapter_raises_for_http_error(
    monkeypatch,
):
    mock_client = MockAsyncClient(
        MockResponse(
            {"error": "Unauthorized"},
            status_code=401,
        )
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.httpx.AsyncClient",
        lambda timeout: mock_client,
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_id",
        "test-app-id",
    )

    monkeypatch.setattr(
        "app.services.job_ingestion.adapters.adzuna.settings.adzuna_app_key",
        "test-app-key",
    )

    adapter = AdzunaAdapter()

    with pytest.raises(httpx.HTTPStatusError):
        await adapter.fetch_jobs()
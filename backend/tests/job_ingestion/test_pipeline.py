import pytest

from app.services.job_ingestion.adapters.base import RawJob
from app.services.job_ingestion.adapters.manual import ManualJobAdapter
from app.services.job_ingestion.pipeline import JobIngestionPipeline


@pytest.mark.asyncio
async def test_manual_adapter_returns_jobs():
    jobs = [
        RawJob(
            source="manual",
            external_id="manual-001",
            title="Software Engineer Intern",
            company="Example Corp",
            location="Bangalore",
            description="Build backend services using Python.",
        )
    ]

    adapter = ManualJobAdapter(jobs)

    result = await adapter.fetch_jobs()

    assert len(result) == 1
    assert result[0].title == "Software Engineer Intern"
    assert result[0].company == "Example Corp"
    assert adapter.source_name == "manual"


@pytest.mark.asyncio
async def test_pipeline_ingests_jobs(session):
    jobs = [
        RawJob(
            source="manual",
            external_id="pipeline-001",
            title="Backend Engineer Intern",
            company="CareerPilot Test",
            location="Remote",
            description="Build APIs using Python and FastAPI.",
        ),
        RawJob(
            source="manual",
            external_id="pipeline-002",
            title="Frontend Engineer Intern",
            company="CareerPilot Test",
            location="Bangalore",
            description="Build React applications.",
        ),
    ]

    adapter = ManualJobAdapter(jobs)
    pipeline = JobIngestionPipeline()

    result = await pipeline.run(session, adapter)

    assert result["source"] == "manual"
    assert result["fetched"] == 2
    assert result["created"] == 2
    assert result["updated"] == 0
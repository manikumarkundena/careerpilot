import pytest
from sqlalchemy import select

from app.models.job import Job
from app.services.job_ingestion.service import JobIngestionService


@pytest.mark.asyncio
async def test_ingest_creates_new_job(session):
    service = JobIngestionService()

    job, created = await service.ingest(
        session,
        source="test_source",
        external_id="job-001",
        title="Software Engineer Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build backend services with Python.",
        application_url=(
            "https://example.com/jobs/001/"
            "?utm_source=linkedin"
        ),
    )

    assert created is True
    assert job.id is not None
    assert job.canonical_url == (
        "https://example.com/jobs/001"
    )
    assert len(job.content_hash) == 64


@pytest.mark.asyncio
async def test_ingest_detects_duplicate_by_external_id(session):
    service = JobIngestionService()

    first_job, first_created = await service.ingest(
        session,
        source="test_source",
        external_id="job-002",
        title="Backend Engineer Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build backend services.",
        application_url="https://example.com/jobs/002",
    )

    second_job, second_created = await service.ingest(
        session,
        source="test_source",
        external_id="job-002",
        title="Backend Engineer Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build backend services.",
        application_url="https://example.com/jobs/002",
    )

    assert first_created is True
    assert second_created is False
    assert first_job.id == second_job.id


@pytest.mark.asyncio
async def test_ingest_detects_duplicate_by_canonical_url(session):
    service = JobIngestionService()

    first_job, first_created = await service.ingest(
        session,
        source="source_a",
        external_id="a-001",
        title="Frontend Engineer Intern",
        company="Example Corp",
        location="Remote",
        description="Build React applications.",
        application_url=(
            "https://example.com/jobs/frontend/"
            "?utm_source=linkedin"
        ),
    )

    second_job, second_created = await service.ingest(
        session,
        source="source_b",
        external_id="b-999",
        title="Frontend Engineer Intern",
        company="Example Corp",
        location="Remote",
        description="Build React applications.",
        application_url=(
            "https://example.com/jobs/frontend/"
            "?utm_campaign=test"
        ),
    )

    assert first_created is True
    assert second_created is False
    assert first_job.id == second_job.id


@pytest.mark.asyncio
async def test_ingest_detects_duplicate_by_content_hash(session):
    service = JobIngestionService()

    first_job, first_created = await service.ingest(
        session,
        source="source_a",
        external_id="hash-001",
        title="Data Engineer Intern",
        company="Example Corp",
        location="Hyderabad",
        description="Build data pipelines using Python.",
    )

    second_job, second_created = await service.ingest(
        session,
        source="source_b",
        external_id="hash-999",
        title=" data engineer intern ",
        company="EXAMPLE CORP",
        location="hyderabad",
        description="Build   data pipelines using Python.",
    )

    assert first_created is True
    assert second_created is False
    assert first_job.id == second_job.id


@pytest.mark.asyncio
async def test_ingest_updates_existing_job(session):
    service = JobIngestionService()

    job, created = await service.ingest(
        session,
        source="test_source",
        external_id="job-update-001",
        title="Software Engineer Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build backend services.",
    )

    assert created is True

    updated_job, updated_created = await service.ingest(
        session,
        source="test_source",
        external_id="job-update-001",
        title="Software Engineer Intern",
        company="Example Corp",
        location="Remote",
        description="Build scalable backend services with Python.",
    )

    assert updated_created is False
    assert updated_job.id == job.id
    assert updated_job.location == "Remote"
    assert "scalable" in updated_job.description


@pytest.mark.asyncio
async def test_ingest_persists_job(session):
    service = JobIngestionService()

    job, created = await service.ingest(
        session,
        source="test_source",
        external_id="persist-001",
        title="ML Engineer Intern",
        company="Example AI",
        location="Remote",
        description="Work on machine learning systems.",
    )

    assert created is True

    result = await session.execute(
        select(Job).where(Job.id == job.id)
    )

    persisted_job = result.scalar_one()

    assert persisted_job.title == "ML Engineer Intern"
    assert persisted_job.company == "Example AI"

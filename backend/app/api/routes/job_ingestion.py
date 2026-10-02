from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.job_ingestion import (
    JobIngestRequest,
    JobIngestResponse,
)
from app.services.job_ingestion.adapters.base import RawJob
from app.services.job_ingestion.adapters.manual import ManualJobAdapter
from app.services.job_ingestion.pipeline import JobIngestionPipeline


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Job Ingestion"],
)


@router.post(
    "/ingest",
    response_model=JobIngestResponse,
)
async def ingest_jobs(
    payload: JobIngestRequest,
    session: AsyncSession = Depends(get_db),
):
    if payload.source != "manual":
        raise HTTPException(
            status_code=404,
            detail=f"No adapter registered for source: {payload.source}",
        )

    raw_jobs = [
        RawJob(
            source=payload.source,
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            description=job.description,
            location=job.location,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            application_url=job.application_url,
        )
        for job in payload.jobs
    ]

    adapter = ManualJobAdapter(raw_jobs)

    pipeline = JobIngestionPipeline()

    return await pipeline.run(
        session,
        adapter,
    )
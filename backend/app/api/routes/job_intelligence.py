from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.job import Job
from app.schemas.job_intelligence import (
    JobAnalyzeRequest,
    JobAnalyzeResponse,
)
from app.services.job_intelligence.service import (
    analyze_and_persist_job,
    analyze_job_description,
)


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Job Intelligence"],
)


@router.post(
    "/analyze",
    response_model=JobAnalyzeResponse,
)
async def analyze_job(
    payload: JobAnalyzeRequest,
    session: AsyncSession = Depends(get_db),
):
    result = await analyze_job_description(
        payload.description,
        session,
    )

    return result


@router.post(
    "/{job_id}/analyze",
    response_model=JobAnalyzeResponse,
)
async def analyze_existing_job(
    job_id: str,
    session: AsyncSession = Depends(get_db),
):
    job = await session.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    result = await analyze_and_persist_job(
        job.id,
        session,
    )

    # Temporary diagnostic output.
    

    return response
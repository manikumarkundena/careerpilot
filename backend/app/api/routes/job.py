from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.job import Job
from app.schemas.job import (
    JobCreateRequest,
    JobListItem,
    JobListResponse,
    JobResponse,
)


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    payload: JobCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    job = Job(
        source=payload.source,
        external_id=payload.external_id,
        title=payload.title,
        company=payload.company,
        location=payload.location,
        description=payload.description,
        employment_type=payload.employment_type,
        experience_level=payload.experience_level,
        application_url=payload.application_url,
        posted_at=payload.posted_at,
        expires_at=payload.expires_at,
        is_active=payload.is_active,
    )

    session.add(job)

    await session.commit()
    await session.refresh(job)

    return JobResponse(
        id=str(job.id),
        source=job.source,
        external_id=job.external_id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        application_url=job.application_url,
        posted_at=job.posted_at,
        expires_at=job.expires_at,
        is_active=job.is_active,
    )


@router.get(
    "",
    response_model=JobListResponse,
)
async def list_jobs(
    source: str | None = Query(
        default=None,
        max_length=100,
    ),
    location: str | None = Query(
        default=None,
        max_length=255,
    ),
    search: str | None = Query(
        default=None,
        max_length=255,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    session: AsyncSession = Depends(get_db),
):
    filters = []

    if source:
        filters.append(Job.source == source)

    if location:
        filters.append(
            Job.location.ilike(f"%{location}%")
        )

    if search:
        search_pattern = f"%{search}%"

        filters.append(
            (
                Job.title.ilike(search_pattern)
                | Job.company.ilike(search_pattern)
                | Job.description.ilike(search_pattern)
            )
        )

    total_query = select(
        func.count()
    ).select_from(Job)

    if filters:
        total_query = total_query.where(*filters)

    total_result = await session.execute(total_query)
    total = total_result.scalar_one()

    offset = (page - 1) * limit

    jobs_query = (
        select(Job)
        .where(*filters)
        .order_by(
            Job.posted_at.desc().nullslast(),
            Job.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(jobs_query)

    jobs = result.scalars().all()

    items = [
        JobListItem(
            id=str(job.id),
            source=job.source,
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            application_url=job.application_url,
            posted_at=job.posted_at,
            is_active=job.is_active,
        )
        for job in jobs
    ]

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )
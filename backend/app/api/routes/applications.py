from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.models.application import JobApplication
from app.models.application_event import ApplicationEvent
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.resume_version import ResumeVersion
from app.models.user import User
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationEventResponse,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationUpdateRequest,
)


router = APIRouter(
    prefix="/api/v1/applications",
    tags=["Applications"],
)


def _to_response(application: JobApplication) -> ApplicationResponse:
    return ApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        job_title=application.job.title,
        company=application.job.company,
        status=application.status,
        notes=application.notes,
        resume_version_id=application.resume_version_id,
        applied_at=application.applied_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


async def _owned_resume_for_job(
    session: AsyncSession,
    user_id: UUID,
    job_id: UUID,
    resume_version_id: UUID,
) -> ResumeVersion:
    result = await session.execute(
        select(ResumeVersion)
        .join(CareerProfile, CareerProfile.id == ResumeVersion.profile_id)
        .where(
            ResumeVersion.id == resume_version_id,
            ResumeVersion.target_job_id == job_id,
            CareerProfile.user_id == user_id,
        )
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Resume version must belong to your career profile "
                "and target the same job"
            ),
        )
    return resume


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    payload: ApplicationCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await session.get(Job, payload.job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    resume = None
    if payload.resume_version_id is not None:
        resume = await _owned_resume_for_job(
            session,
            current_user.id,
            job.id,
            payload.resume_version_id,
        )

    existing = await session.execute(
        select(JobApplication).where(
            JobApplication.user_id == current_user.id,
            JobApplication.job_id == payload.job_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An application tracker entry already exists for this job",
        )

    application = JobApplication(
        user_id=current_user.id,
        job_id=job.id,
        resume_version_id=resume.id if resume else None,
        status=payload.status,
        notes=payload.notes,
        applied_at=(
            datetime.now(timezone.utc)
            if payload.status != "saved"
            else None
        ),
    )
    session.add(application)
    await session.flush()
    session.add(
        ApplicationEvent(
            application_id=application.id,
            actor_user_id=current_user.id,
            event_type="created",
            to_status=application.status,
            details="Application tracker entry created",
        )
    )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        # Handles two concurrent create requests racing past the pre-check.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An application tracker entry already exists for this job",
        ) from exc

    await session.refresh(application)
    application.job = job
    return _to_response(application)


@router.get(
    "",
    response_model=ApplicationListResponse,
)
async def list_applications(
    application_status: ApplicationStatus | None = Query(
        default=None,
        alias="status",
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = [JobApplication.user_id == current_user.id]
    if application_status is not None:
        filters.append(JobApplication.status == application_status)

    total_result = await session.execute(
        select(func.count(JobApplication.id)).where(*filters)
    )
    total = total_result.scalar_one()

    result = await session.execute(
        select(JobApplication)
        .options(joinedload(JobApplication.job))
        .where(*filters)
        .order_by(
            JobApplication.updated_at.desc(),
            JobApplication.created_at.desc(),
        )
        .offset((page - 1) * limit)
        .limit(limit)
    )
    applications = result.scalars().all()

    return ApplicationListResponse(
        items=[_to_response(item) for item in applications],
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
async def get_application(
    application_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(JobApplication)
        .options(joinedload(JobApplication.job))
        .where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return _to_response(application)


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
)
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(JobApplication)
        .options(joinedload(JobApplication.job))
        .where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    changes = payload.model_dump(exclude_unset=True)
    previous_status = application.status
    previous_notes = application.notes
    previous_resume_version_id = application.resume_version_id

    if "status" in changes and changes["status"] is not None:
        new_status = changes["status"]
        if new_status != "saved" and application.applied_at is None:
            application.applied_at = datetime.now(timezone.utc)
        application.status = new_status
    if "notes" in changes:
        application.notes = changes["notes"]
    if "resume_version_id" in changes:
        resume_version_id = changes["resume_version_id"]
        if resume_version_id is None:
            application.resume_version_id = None
        else:
            resume = await _owned_resume_for_job(
                session,
                current_user.id,
                application.job_id,
                resume_version_id,
            )
            application.resume_version_id = resume.id

    if application.status != previous_status:
        session.add(
            ApplicationEvent(
                application_id=application.id,
                actor_user_id=current_user.id,
                event_type="status_changed",
                from_status=previous_status,
                to_status=application.status,
            )
        )
    if application.notes != previous_notes:
        session.add(
            ApplicationEvent(
                application_id=application.id,
                actor_user_id=current_user.id,
                event_type="notes_updated",
                details="Application notes updated",
            )
        )
    if application.resume_version_id != previous_resume_version_id:
        session.add(
            ApplicationEvent(
                application_id=application.id,
                actor_user_id=current_user.id,
                event_type=(
                    "resume_attached"
                    if application.resume_version_id is not None
                    else "resume_detached"
                ),
                details="Linked resume version changed",
            )
        )

    await session.commit()
    await session.refresh(application)
    return _to_response(application)



@router.get(
    "/{application_id}/events",
    response_model=list[ApplicationEventResponse],
)
async def list_application_events(
    application_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's application audit trail, newest first."""
    application_result = await session.execute(
        select(JobApplication.id).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )
    if application_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    events_result = await session.execute(
        select(ApplicationEvent)
        .where(ApplicationEvent.application_id == application_id)
        .order_by(
            ApplicationEvent.created_at.desc(),
            ApplicationEvent.id.desc(),
        )
    )
    return events_result.scalars().all()

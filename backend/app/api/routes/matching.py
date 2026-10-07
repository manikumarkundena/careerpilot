from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.embedding import get_embedding_provider
from app.db.database import get_db
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.user import User
from app.schemas.matching import MatchResponse, RankedJobMatchItem, RankedJobMatchResponse
from app.services.matching.service import (
    match_candidate_to_job_from_db,
)


router = APIRouter(
    prefix="/api/v1/matching",
    tags=["matching"],
)


@router.post(
    "/jobs/{job_id}",
    response_model=MatchResponse,
)
async def match_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embedding_provider = Depends(get_embedding_provider),
):
    """
    Match the authenticated user's career profile against a job.
    """

    profile_result = await session.execute(
        select(CareerProfile).where(
            CareerProfile.user_id == current_user.id
        )
    )

    profile = profile_result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career profile not found",
        )

    job_result = await session.execute(
        select(Job.id).where(Job.id == job_id)
    )

    job_exists = job_result.scalar_one_or_none()

    if job_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    match_result = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job_id,
        session=session,
        embedding_provider=embedding_provider,
    )

    if match_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to calculate job match",
        )

    return MatchResponse(
        job_id=job_id,
        score=match_result.score,
        semantic_similarity=match_result.semantic_similarity,
        skill_coverage=match_result.skill_coverage,
        requirement_coverage=(
            match_result.requirement_coverage
        ),
        matched_skills=match_result.matched_skills,
        missing_skills=match_result.missing_skills,
        matched_requirements=[
            {
                "requirement_text": (
                    item.requirement_text
                ),
                "requirement_type": (
                    item.requirement_type
                ),
                "importance": item.importance,
                "matched": item.matched,
                "matched_skills": item.matched_skills,
            }
            for item in match_result.matched_requirements
        ],
        gaps=match_result.gaps,
    )


@router.get(
    "/jobs",
    response_model=RankedJobMatchResponse,
)
async def rank_matching_jobs(
    location: str | None = Query(default=None, max_length=255),
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embedding_provider = Depends(get_embedding_provider),
):
    """Return the best active jobs for the authenticated candidate."""
    profile_result = await session.execute(
        select(CareerProfile).where(CareerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career profile not found",
        )

    ranked = await rank_jobs_for_candidate(
        profile_id=profile.id,
        session=session,
        embedding_provider=embedding_provider,
        location=location,
        search=search,
        limit=limit,
    )
    if ranked is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to calculate job matches",
        )

    return RankedJobMatchResponse(
        items=[
            RankedJobMatchItem(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                application_url=job.application_url,
                score=match.score,
                semantic_similarity=match.semantic_similarity,
                skill_coverage=match.skill_coverage,
                requirement_coverage=match.requirement_coverage,
                matched_skills=match.matched_skills,
                missing_skills=match.missing_skills,
            )
            for job, match in ranked
        ],
        total=len(ranked),
    )

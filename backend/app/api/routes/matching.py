from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.schemas.matching import MatchResponse
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
    session: AsyncSession = Depends(get_db),
):
    """
    Match the development candidate profile against a job.

    Authentication/user scoping will replace the temporary
    candidate resolution once authentication is introduced.
    """

    # --------------------------------------------------------
    # Temporary development candidate resolution
    # --------------------------------------------------------

    result = await session.execute(
        select(CareerProfile)
        .order_by(CareerProfile.id)
        .limit(1)
    )

    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career profile not found",
        )

    # --------------------------------------------------------
    # Verify that the requested job exists
    # --------------------------------------------------------

    job_result = await session.execute(
        select(Job.id).where(Job.id == job_id)
    )

    job_exists = job_result.scalar_one_or_none()

    if job_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # --------------------------------------------------------
    # Run matching engine
    # --------------------------------------------------------

    match_result = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job_id,
        session=session,
    )

    if match_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to calculate job match",
        )

    # --------------------------------------------------------
    # Build API response
    # --------------------------------------------------------

    return MatchResponse(
        job_id=job_id,
        score=match_result.score,
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
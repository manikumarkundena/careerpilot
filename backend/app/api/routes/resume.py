from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.skill import Skill
from app.models.user import User
from app.schemas.resume import ResumeGenerateRequest
from app.services.resume.generation import (
    ResumeGenerationArtifactError,
    ResumeGenerationQualityError,
    ResumeGenerationValidationError,
    generate_resume_pdf,
)


router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["Resumes"],
)


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Generated role-specific PDF resume.",
        }
    },
)
async def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    profile = await _load_profile(session, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career profile not found",
        )

    job = await _load_job(session, payload.job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    try:
        result = generate_resume_pdf(profile, job)
    except ResumeGenerationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Generated resume failed validation",
                "issues": [
                    {
                        "code": issue.code,
                        "message": issue.message,
                        "source": issue.source,
                    }
                    for issue in exc.issues
                ],
            },
        ) from exc
    except ResumeGenerationQualityError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Generated resume failed quality checks",
                "keyword_coverage": exc.report.keyword_coverage,
                "issues": [
                    {
                        "code": issue.code,
                        "severity": issue.severity,
                        "message": issue.message,
                    }
                    for issue in exc.report.issues
                ],
            },
        ) from exc
    except ResumeGenerationArtifactError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Generated PDF failed artifact validation",
                "missing_expected_text": list(
                    exc.report.missing_expected_text
                ),
            },
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Resume PDF generation is temporarily unavailable",
        ) from exc

    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="careerpilot-resume.pdf"'
            ),
            "Cache-Control": "private, no-store",
            "X-Resume-Keyword-Coverage": str(
                result.quality.keyword_coverage
            ),
            "X-Resume-Quality-Passed": str(
                result.quality.passed
            ).lower(),
        },
    )


async def _load_profile(
    session: AsyncSession,
    user_id: UUID,
):
    result = await session.execute(
        select(CareerProfile)
        .where(CareerProfile.user_id == user_id)
        .options(
            selectinload(CareerProfile.user),
            selectinload(CareerProfile.education),
            selectinload(CareerProfile.experience),
            selectinload(CareerProfile.skills).selectinload(Skill.skill),
            selectinload(CareerProfile.projects),
            selectinload(CareerProfile.certifications),
            selectinload(CareerProfile.achievements),
            selectinload(CareerProfile.links),
            selectinload(CareerProfile.preferences),
        )
    )
    return result.scalar_one_or_none()


async def _load_job(
    session: AsyncSession,
    job_id: UUID,
):
    result = await session.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(
            selectinload(Job.requirements)
            .selectinload(JobRequirement.skills)
            .selectinload(JobRequirementSkill.skill),
        )
    )
    return result.scalar_one_or_none()

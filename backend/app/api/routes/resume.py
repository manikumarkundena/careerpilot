from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.resume_version import ResumeVersion
from app.models.skill import Skill
from app.models.user import User
from app.schemas.resume import ResumeGenerateRequest
from app.services.resume.ai_optimizer import ResumeOptimizationValidationError
from app.services.resume.generation import (
    ResumeGenerationArtifactError,
    ResumeGenerationQualityError,
    ResumeGenerationValidationError,
    ResumeOptimizationConfigurationError,
    ResumeOptimizationProviderError,
    ResumeOptimizationTimeoutError,
    generate_resume_pdf,
)
from app.services.resume.persistence import persist_resume_version


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
        result = generate_resume_pdf(
            profile,
            job,
            optimize_with_ai=payload.optimize_with_ai,
        )
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
    except ResumeOptimizationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI resume optimization is not configured on this server",
        ) from exc
    except ResumeOptimizationTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI resume optimization provider timed out; please retry",
        ) from exc
    except ResumeOptimizationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI resume optimization returned an invalid response",
        ) from exc
    except ResumeOptimizationProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI resume optimization provider is temporarily unavailable",
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

    resume = await persist_resume_version(
        session=session,
        profile_id=profile.id,
        target_job_id=job.id,
        result=result,
    )
    await session.commit()

    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="careerpilot-resume.pdf"'
            ),
            "Cache-Control": "private, no-store",
            "X-Resume-Version": str(resume.version),
            "X-Resume-Keyword-Coverage": str(
                result.quality.keyword_coverage
            ),
            "X-Resume-Quality-Passed": str(
                result.quality.passed
            ).lower(),
            "X-Resume-AI-Optimized": str(result.ai_optimized).lower(),
        },
    )


@router.get("")
async def list_resume_versions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    profile = await _load_profile(session, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Career profile not found")

    result = await session.execute(
        select(ResumeVersion)
        .where(ResumeVersion.profile_id == profile.id)
        .order_by(desc(ResumeVersion.version))
    )
    versions = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "version": item.version,
            "target_job_id": str(item.target_job_id),
            "template_version": item.template_version,
            "pdf_sha256": item.pdf_sha256,
            "generated_at": item.generated_at,
        }
        for item in versions
    ]


@router.get("/{resume_id}")
async def get_resume_version(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    profile = await _load_profile(session, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Career profile not found")

    result = await session.execute(
        select(ResumeVersion).where(
            ResumeVersion.id == resume_id,
            ResumeVersion.profile_id == profile.id,
        )
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume version not found")

    return {
        "id": str(resume.id),
        "version": resume.version,
        "target_job_id": str(resume.target_job_id),
        "template_version": resume.template_version,
        "document": resume.document_json,
        "quality": resume.quality_report_json,
        "pdf_sha256": resume.pdf_sha256,
        "generated_at": resume.generated_at,
    }


@router.get("/{resume_id}/pdf")
async def download_resume_version(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    profile = await _load_profile(session, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Career profile not found")

    result = await session.execute(
        select(ResumeVersion).where(
            ResumeVersion.id == resume_id,
            ResumeVersion.profile_id == profile.id,
        )
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume version not found")

    return Response(
        content=resume.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="careerpilot-resume-v{resume.version}.pdf"'
            ),
            "Cache-Control": "private, no-store",
            "X-Resume-Version": str(resume.version),
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

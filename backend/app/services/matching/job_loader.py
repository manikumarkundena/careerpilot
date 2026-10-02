from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill


@dataclass(slots=True)
class JobRequirementSnapshot:
    requirement_id: UUID
    requirement_type: str
    text: str
    importance: float
    skills: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JobSnapshot:
    job_id: UUID
    title: str
    company: str | None
    location: str | None
    description: str | None
    employment_type: str | None
    experience_level: str | None
    requirements: list[JobRequirementSnapshot] = field(
        default_factory=list
    )
    required_skills: list[str] = field(default_factory=list)


async def load_job_snapshot(
    job_id: UUID,
    session: AsyncSession,
) -> JobSnapshot | None:
    result = await session.execute(
        select(Job)
        .options(
            selectinload(Job.requirements)
            .selectinload(JobRequirement.skills)
            .selectinload(JobRequirementSkill.skill)
        )
        .where(Job.id == job_id)
    )

    job = result.scalar_one_or_none()

    if job is None:
        return None

    requirements: list[JobRequirementSnapshot] = []
    required_skills: list[str] = []

    for requirement in job.requirements:
        skills = [
            requirement_skill.skill.name
            for requirement_skill in requirement.skills
        ]

        requirements.append(
            JobRequirementSnapshot(
                requirement_id=requirement.id,
                requirement_type=requirement.requirement_type,
                text=requirement.text,
                importance=(
                    requirement.importance
                    if requirement.importance is not None
                    else 0.5
                ),
                skills=skills,
            )
        )

        required_skills.extend(skills)

    # Remove duplicate skills while preserving order.
    required_skills = list(dict.fromkeys(required_skills))

    return JobSnapshot(
        job_id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        requirements=requirements,
        required_skills=required_skills,
    )

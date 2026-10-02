import uuid

import pytest

from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.skill_catalog import SkillCatalog
from app.services.matching.job_loader import load_job_snapshot


async def get_or_create_skill(
    session,
    *,
    name: str,
    category: str,
) -> SkillCatalog:
    from sqlalchemy import select

    result = await session.execute(
        select(SkillCatalog).where(
            SkillCatalog.name == name
        )
    )

    skill = result.scalar_one_or_none()

    if skill is None:
        skill = SkillCatalog(
            name=name,
            category=category,
            is_active=True,
        )

        session.add(skill)
        await session.flush()

    return skill


@pytest.mark.asyncio
async def test_load_job_snapshot(session):
    python = await get_or_create_skill(
        session,
        name="Python",
        category="Programming Language",
    )

    fastapi = await get_or_create_skill(
        session,
        name="FastAPI",
        category="Backend",
    )

    docker = await get_or_create_skill(
        session,
        name="Docker",
        category="DevOps",
    )

    job = Job(
        source="test",
        external_id=f"matching-{uuid.uuid4()}",
        canonical_url=f"https://example.com/jobs/{uuid.uuid4()}",
        title="Backend Software Engineer",
        company="CareerPilot Test",
        location="Bengaluru",
        description=(
            "Build backend services using Python and FastAPI."
        ),
        employment_type="Full-time",
        experience_level="Entry-level",
        application_url="https://example.com/apply",
    )

    session.add(job)
    await session.flush()

    backend_requirement = JobRequirement(
        job_id=job.id,
        requirement_type="required",
        text="Strong Python and FastAPI experience",
        importance=1.0,
    )

    docker_requirement = JobRequirement(
        job_id=job.id,
        requirement_type="preferred",
        text="Docker experience is preferred",
        importance=0.5,
    )

    session.add_all(
        [
            backend_requirement,
            docker_requirement,
        ]
    )

    await session.flush()

    session.add_all(
        [
            JobRequirementSkill(
                requirement_id=backend_requirement.id,
                skill_id=python.id,
            ),
            JobRequirementSkill(
                requirement_id=backend_requirement.id,
                skill_id=fastapi.id,
            ),
            JobRequirementSkill(
                requirement_id=docker_requirement.id,
                skill_id=docker.id,
            ),
        ]
    )

    await session.commit()

    snapshot = await load_job_snapshot(
        job.id,
        session,
    )

    assert snapshot is not None

    assert snapshot.job_id == job.id

    assert snapshot.title == "Backend Software Engineer"

    assert snapshot.company == "CareerPilot Test"

    assert snapshot.location == "Bengaluru"

    assert len(snapshot.requirements) == 2

    assert snapshot.required_skills == [
        "Python",
        "FastAPI",
        "Docker",
    ]

    first_requirement = snapshot.requirements[0]

    assert first_requirement.requirement_type == "required"

    assert (
        first_requirement.text
        == "Strong Python and FastAPI experience"
    )

    assert first_requirement.importance == 1.0

    assert first_requirement.skills == [
        "Python",
        "FastAPI",
    ]

    second_requirement = snapshot.requirements[1]

    assert second_requirement.requirement_type == "preferred"

    assert second_requirement.skills == [
        "Docker"
    ]

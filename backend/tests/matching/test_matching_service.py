import uuid

import pytest
from sqlalchemy import select

from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.skill import Skill
from app.models.skill_catalog import SkillCatalog
from app.services.matching.service import (
    match_candidate_to_job_from_db,
)
from tests.conftest import create_test_user


async def get_or_create_skill(
    session,
    *,
    name: str,
    category: str,
) -> SkillCatalog:
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


# ============================================================
# DB-BACKED CANDIDATE ↔ JOB MATCHING
# ============================================================


@pytest.mark.asyncio
async def test_match_candidate_to_job_from_db(session):
    # ========================================================
    # Candidate
    # ========================================================

    user = create_test_user(
        email=f"match-{uuid.uuid4()}@example.com"
    )

    session.add(user)
    await session.flush()

    profile = CareerProfile(
        user_id=user.id,
        headline="Backend Developer",
        summary="Python backend developer",
        target_roles="Backend Engineer",
    )

    session.add(profile)
    await session.flush()

    # --------------------------------------------------------
    # Candidate skills
    # --------------------------------------------------------

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

    session.add_all(
        [
            Skill(
                profile_id=profile.id,
                skill_id=python.id,
                proficiency="Advanced",
            ),
            Skill(
                profile_id=profile.id,
                skill_id=fastapi.id,
                proficiency="Intermediate",
            ),
        ]
    )

    # ========================================================
    # Job
    # ========================================================

    job = Job(
        source="test",
        external_id=f"job-{uuid.uuid4()}",
        canonical_url=(
            f"https://example.com/jobs/{uuid.uuid4()}"
        ),
        title="Backend Software Engineer",
        company="CareerPilot Test",
        location="Bengaluru",
        description=(
            "Build backend services using Python "
            "and FastAPI."
        ),
        employment_type="Full-time",
        experience_level="Entry-level",
        application_url="https://example.com/apply",
    )

    session.add(job)
    await session.flush()

    # --------------------------------------------------------
    # Job requirements
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Requirement → Skill relationships
    # --------------------------------------------------------

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

    # ========================================================
    # Actual DB-backed matching
    # ========================================================

    result = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job.id,
        session=session,
    )

    # ========================================================
    # Assertions
    # ========================================================

    assert result is not None

    # Candidate has Python + FastAPI.
    # Job requires Python + FastAPI + Docker.
    assert result.skill_coverage == pytest.approx(
        2 / 3,
        abs=0.0001,
    )

    # Python/FastAPI requirement = 1.0
    # Docker requirement = 0.5
    #
    # Candidate matches 1.0 / 1.5 total weight.
    assert result.requirement_coverage == pytest.approx(
        1 / 1.5,
        abs=0.0001,
    )

    assert set(result.matched_skills) == {
        "Python",
        "FastAPI",
    }

    assert result.missing_skills == [
        "Docker"
    ]

    assert len(result.matched_requirements) == 2

    assert (
        result.matched_requirements[0].matched
        is True
    )

    assert (
        result.matched_requirements[1].matched
        is False
    )

    assert result.gaps == [
        "Missing skill: Docker"
    ]


# ============================================================
# MISSING JOB
# ============================================================


@pytest.mark.asyncio
async def test_match_candidate_to_missing_job(
    session,
):
    user = create_test_user(
        email=f"missing-job-{uuid.uuid4()}@example.com"
    )

    session.add(user)
    await session.flush()

    profile = CareerProfile(
        user_id=user.id,
        headline="Backend Developer",
    )

    session.add(profile)
    await session.flush()

    result = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=uuid.uuid4(),
        session=session,
    )

    assert result is None


# ============================================================
# MISSING CANDIDATE
# ============================================================


@pytest.mark.asyncio
async def test_match_missing_candidate_to_job(
    session,
):
    job = Job(
        source="test",
        external_id=f"job-{uuid.uuid4()}",
        canonical_url=(
            f"https://example.com/jobs/{uuid.uuid4()}"
        ),
        title="Backend Engineer",
        company="CareerPilot Test",
        description=(
            "Backend engineering role for testing."
        ),
    )

    session.add(job)
    await session.commit()

    result = await match_candidate_to_job_from_db(
        profile_id=uuid.uuid4(),
        job_id=job.id,
        session=session,
    )

    assert result is None
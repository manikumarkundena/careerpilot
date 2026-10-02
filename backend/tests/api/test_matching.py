import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.database import get_db
from app.main import app
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.skill import Skill
from app.models.skill_catalog import SkillCatalog
from app.models.user import User


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
# MATCHING API
# ============================================================


@pytest.mark.asyncio
async def test_match_job_api(
    session,
    override_get_db,
):
    # ========================================================
    # Candidate
    # ========================================================

    user = User(
        email=f"api-match-{uuid.uuid4()}@example.com"
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
        external_id=f"api-job-{uuid.uuid4()}",
        canonical_url=(
            f"https://example.com/jobs/{uuid.uuid4()}"
        ),
        title="Backend Engineer",
        company="CareerPilot Test",
        location="Bengaluru",
        description=(
            "Python and FastAPI backend role."
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
        text="Python and FastAPI",
        importance=1.0,
    )

    docker_requirement = JobRequirement(
        job_id=job.id,
        requirement_type="preferred",
        text="Docker",
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
    # API request
    # ========================================================

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/matching/jobs/{job.id}"
        )

    # ========================================================
    # Assertions
    # ========================================================

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == str(job.id)

    assert data["skill_coverage"] == pytest.approx(
        2 / 3,
        abs=0.0001,
    )

    assert data["requirement_coverage"] == pytest.approx(
        1 / 1.5,
        abs=0.0001,
    )

    assert set(data["matched_skills"]) == {
        "Python",
        "FastAPI",
    }

    assert data["missing_skills"] == [
        "Docker"
    ]

    assert data["gaps"] == [
        "Missing skill: Docker"
    ]


# ============================================================
# MISSING PROFILE
# ============================================================


@pytest.mark.asyncio
async def test_match_job_api_returns_404_for_missing_profile(
    session,
    override_get_db,
):
    # --------------------------------------------------------
    # The test fixture may contain data created by other tests.
    # Remove all career profiles/users for this isolated case.
    # --------------------------------------------------------

    await session.execute(
        CareerProfile.__table__.delete()
    )

    await session.execute(
        User.__table__.delete()
    )

    await session.commit()

    job_id = uuid.uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/matching/jobs/{job_id}"
        )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Career profile not found"
    )


# ============================================================
# MISSING JOB
# ============================================================


@pytest.mark.asyncio
async def test_match_job_api_returns_404_for_missing_job(
    session,
    override_get_db,
):
    # --------------------------------------------------------
    # Create a valid candidate profile.
    # --------------------------------------------------------

    user = User(
        email=f"missing-api-job-{uuid.uuid4()}@example.com"
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
    await session.commit()

    # --------------------------------------------------------
    # Use a job ID that does not exist.
    # --------------------------------------------------------

    missing_job_id = uuid.uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/matching/jobs/{missing_job_id}"
        )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Job not found"
    )
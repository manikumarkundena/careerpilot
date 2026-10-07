import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.api.dependencies.embedding import get_embedding_provider
from app.db.database import get_db
from app.main import app
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill
from app.models.skill import Skill
from app.models.skill_catalog import SkillCatalog
from app.models.user import User
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

    user = create_test_user(
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

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/matching/jobs/{job.id}",
            headers={"Authorization": f"Bearer {token}"},
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

    user = create_test_user(
        email=f"missing-profile-{uuid.uuid4()}@example.com"
    )
    session.add(user)
    await session.commit()

    token = create_access_token(user.id)
    job_id = uuid.uuid4()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/matching/jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
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

    user = create_test_user(
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

    token = create_access_token(user.id)

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
            f"/api/v1/matching/jobs/{missing_job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Job not found"
    )

# ============================================================
# AUTHENTICATION / USER ISOLATION
# ============================================================


@pytest.mark.asyncio
async def test_match_job_api_requires_authentication(
    session,
    override_get_db,
):
    job = Job(
        source="test",
        external_id=f"unauth-job-{uuid.uuid4()}",
        canonical_url=(
            f"https://example.com/jobs/{uuid.uuid4()}"
        ),
        title="Backend Engineer",
        company="CareerPilot Test",
        description="Backend engineering role.",
    )

    session.add(job)
    await session.commit()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/matching/jobs/{job.id}"
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Authentication required"
    )


@pytest.mark.asyncio
async def test_match_job_api_uses_authenticated_users_profile(
    session,
    override_get_db,
):
    user_a = create_test_user(
        email=f"user-a-{uuid.uuid4()}@example.com"
    )
    user_b = create_test_user(
        email=f"user-b-{uuid.uuid4()}@example.com"
    )

    session.add_all([user_a, user_b])
    await session.flush()

    profile_a = CareerProfile(
        user_id=user_a.id,
        headline="Python Developer",
    )
    profile_b = CareerProfile(
        user_id=user_b.id,
        headline="Java Developer",
    )

    session.add_all([profile_a, profile_b])
    await session.flush()

    python = await get_or_create_skill(
        session,
        name="Python",
        category="Programming Language",
    )
    java = await get_or_create_skill(
        session,
        name="Java",
        category="Programming Language",
    )

    session.add_all(
        [
            Skill(
                profile_id=profile_a.id,
                skill_id=python.id,
                proficiency="Advanced",
            ),
            Skill(
                profile_id=profile_b.id,
                skill_id=java.id,
                proficiency="Advanced",
            ),
        ]
    )

    job = Job(
        source="test",
        external_id=f"isolation-job-{uuid.uuid4()}",
        canonical_url=(
            f"https://example.com/jobs/{uuid.uuid4()}"
        ),
        title="Java Backend Engineer",
        company="CareerPilot Test",
        description="Java backend engineering role.",
    )

    session.add(job)
    await session.flush()

    requirement = JobRequirement(
        job_id=job.id,
        requirement_type="required",
        text="Strong Java experience",
        importance=1.0,
    )

    session.add(requirement)
    await session.flush()

    session.add(
        JobRequirementSkill(
            requirement_id=requirement.id,
            skill_id=java.id,
        )
    )

    await session.commit()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response_a = await client.post(
            f"/api/v1/matching/jobs/{job.id}",
            headers={
                "Authorization": f"Bearer {token_a}"
            },
        )

        response_b = await client.post(
            f"/api/v1/matching/jobs/{job.id}",
            headers={
                "Authorization": f"Bearer {token_b}"
            },
        )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert response_a.json()["skill_coverage"] == 0.0
    assert response_b.json()["skill_coverage"] == 1.0

    assert response_a.json()["matched_skills"] == []
    assert response_b.json()["matched_skills"] == ["Java"]


@pytest.mark.asyncio
async def test_match_job_api_uses_configured_semantic_provider(
    session,
    override_get_db,
):
    class FakeEmbeddingProvider:
        async def embed(self, text: str) -> list[float]:
            vector = [0.0] * 1536
            vector[0] = 1.0
            return vector

    user = create_test_user(
        email=f"semantic-api-{uuid.uuid4()}@example.com"
    )
    session.add(user)
    await session.flush()

    profile = CareerProfile(
        user_id=user.id,
        headline="Python Developer",
        summary="Backend developer",
        target_roles="Backend Engineer",
    )
    session.add(profile)
    await session.flush()

    java = await get_or_create_skill(
        session,
        name="Java",
        category="Programming Language",
    )

    job = Job(
        source="test",
        external_id=f"semantic-api-job-{uuid.uuid4()}",
        canonical_url=f"https://example.com/jobs/{uuid.uuid4()}",
        title="Java Backend Engineer",
        company="CareerPilot Test",
        description="Build Java backend services.",
    )
    session.add(job)
    await session.flush()

    requirement = JobRequirement(
        job_id=job.id,
        requirement_type="required",
        text="Strong Java experience",
        importance=1.0,
    )
    session.add(requirement)
    await session.flush()
    session.add(
        JobRequirementSkill(
            requirement_id=requirement.id,
            skill_id=java.id,
        )
    )
    await session.commit()

    app.dependency_overrides[get_embedding_provider] = (
        lambda: FakeEmbeddingProvider()
    )

    try:
        token = create_access_token(user.id)
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/matching/jobs/{job.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.pop(get_embedding_provider, None)

    assert response.status_code == 200
    data = response.json()
    assert data["semantic_similarity"] == pytest.approx(1.0)
    assert data["score"] == pytest.approx(20.0)

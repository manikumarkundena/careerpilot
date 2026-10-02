import uuid

import pytest
from sqlalchemy import select

from app.models.career_profile import CareerProfile
from app.models.skill import Skill
from app.models.skill_catalog import SkillCatalog
from app.models.user import User
from app.services.matching.candidate_loader import load_candidate_snapshot


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


@pytest.mark.asyncio
async def test_load_candidate_snapshot(session):
    # -------------------------
    # Create user
    # -------------------------
    user = User(
        email=f"matching-{uuid.uuid4()}@example.com"
    )

    session.add(user)
    await session.flush()

    # -------------------------
    # Create career profile
    # -------------------------
    profile = CareerProfile(
        user_id=user.id,
        headline="Backend Developer",
        summary="Python backend developer",
        target_roles="Software Engineer, Backend Engineer",
    )

    session.add(profile)
    await session.flush()

    # -------------------------
    # Reuse/create skills
    # -------------------------
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

    # -------------------------
    # Add profile skills
    # -------------------------
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

    await session.commit()

    # -------------------------
    # Load candidate snapshot
    # -------------------------
    snapshot = await load_candidate_snapshot(
        profile.id,
        session,
    )

    # -------------------------
    # Assertions
    # -------------------------
    assert snapshot is not None

    assert snapshot.profile_id == profile.id

    assert snapshot.headline == "Backend Developer"

    assert snapshot.summary == "Python backend developer"

    assert (
        snapshot.target_roles
        == "Software Engineer, Backend Engineer"
    )

    assert snapshot.skills == {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
    }

    assert snapshot.education == []

    assert snapshot.experience == []

    assert snapshot.projects == []

    assert snapshot.certifications == []

    assert snapshot.preferences is None
import uuid

import pytest
from sqlalchemy import select

from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.services.matching.embeddings import EmbeddingError
from app.services.matching.service import match_candidate_to_job_from_db
from app.models.semantic_embedding import SemanticEmbedding
from tests.conftest import create_test_user


DIMENSION = 1536


class FakeEmbeddingProvider:
    def __init__(self):
        self.calls = []

    async def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        vector = [0.0] * DIMENSION
        if "Backend Developer" in text:
            vector[0] = 1.0
        elif "Backend Engineer" in text:
            vector[0] = 1.0
        else:
            vector[1] = 1.0
        return vector


class FailingEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        raise EmbeddingError("embedding service unavailable")


async def create_candidate_and_job(session):
    user = create_test_user(
        email=f"semantic-{uuid.uuid4()}@example.com"
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

    job = Job(
        source="test",
        external_id=f"semantic-job-{uuid.uuid4()}",
        canonical_url=f"https://example.com/jobs/{uuid.uuid4()}",
        title="Backend Engineer",
        company="CareerPilot Semantic Test",
        location="Bengaluru",
        description="Build backend services with Python.",
        employment_type="Full-time",
        experience_level="Entry-level",
        application_url="https://example.com/apply",
    )
    session.add(job)
    await session.flush()

    session.add(
        JobRequirement(
            job_id=job.id,
            requirement_type="skill",
            text="Production Java experience",
            importance=1.0,
        )
    )
    await session.commit()

    return profile, job


@pytest.mark.asyncio
async def test_db_matching_persists_and_reuses_semantic_embeddings(session):
    profile, job = await create_candidate_and_job(session)
    provider = FakeEmbeddingProvider()

    first = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job.id,
        session=session,
        embedding_provider=provider,
    )

    assert first is not None
    assert first.semantic_similarity == pytest.approx(1.0)
    assert first.score == pytest.approx(100.0)
    assert len(provider.calls) == 2

    stored = (
        await session.execute(
            select(SemanticEmbedding).order_by(
                SemanticEmbedding.entity_type
            )
        )
    ).scalars().all()

    assert len(stored) == 2
    assert {item.entity_type for item in stored} == {
        "career_profile",
        "job",
    }
    assert all(item.dimension == DIMENSION for item in stored)
    assert all(len(item.embedding) == DIMENSION for item in stored)

    second = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job.id,
        session=session,
        embedding_provider=provider,
    )

    assert second is not None
    assert second.semantic_similarity == pytest.approx(1.0)
    assert second.score == pytest.approx(100.0)
    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_db_matching_refreshes_only_changed_embedding(session):
    profile, job = await create_candidate_and_job(session)
    provider = FakeEmbeddingProvider()

    await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job.id,
        session=session,
        embedding_provider=provider,
    )
    assert len(provider.calls) == 2

    job.description = "Build distributed Java backend services."
    await session.commit()

    refreshed = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job.id,
        session=session,
        embedding_provider=provider,
    )

    assert refreshed is not None
    assert refreshed.semantic_similarity == pytest.approx(1.0)
    assert len(provider.calls) == 3

    rows = (
        await session.execute(
            select(SemanticEmbedding).where(
                SemanticEmbedding.entity_type == "job",
                SemanticEmbedding.entity_id == job.id,
            )
        )
    ).scalars().all()

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_db_matching_falls_back_when_embedding_provider_fails(session):
    profile, job = await create_candidate_and_job(session)

    result = await match_candidate_to_job_from_db(
        profile_id=profile.id,
        job_id=job.id,
        session=session,
        embedding_provider=FailingEmbeddingProvider(),
    )

    assert result is not None
    assert result.semantic_similarity is None

    # No semantic contribution means the deterministic 60/40
    # compatibility score remains in effect. The fixture has one
    # unmatched requirement, so skill coverage is 1.0 and requirement
    # coverage is 0.0 -> 60/40 score = 60.0.
    assert result.score == pytest.approx(60.0)

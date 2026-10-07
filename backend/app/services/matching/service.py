from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.job_requirement_skill import JobRequirementSkill

from app.services.matching.candidate_loader import (
    load_candidate_snapshot,
)
from app.services.matching.job_loader import (
    load_job_snapshot,
)
from app.services.matching.models import MatchResult
from app.services.matching.requirement_matcher import (
    match_requirement,
)
from app.services.matching.skill_matcher import match_skills
from app.services.matching.semantic_text import (
    build_candidate_semantic_text,
    build_job_semantic_text,
)
from app.services.matching.embedding_store import get_or_create_embedding
from app.services.matching.embeddings import EmbeddingError, EmbeddingProvider
from app.services.matching.hybrid import calculate_semantic_similarity


def calculate_skill_coverage(
    candidate_skills,
    required_skills,
) -> float:
    if not required_skills:
        return 1.0

    normalized_candidate = {
        skill.strip().lower()
        for skill in candidate_skills
    }

    matched = sum(
        1
        for skill in required_skills
        if skill.strip().lower() in normalized_candidate
    )

    return matched / len(required_skills)


def calculate_requirement_coverage(
    requirements,
) -> float:
    if not requirements:
        return 1.0

    total_weight = sum(
        max(requirement.importance, 0.0)
        for requirement in requirements
    )

    if total_weight == 0:
        return 0.0

    matched_weight = sum(
        max(requirement.importance, 0.0)
        for requirement in requirements
        if requirement.matched
    )

    return matched_weight / total_weight


def match_candidate_to_job(
    *,
    candidate_skills: dict[str, str | None],
    required_skills: list[str],
    requirements: list[dict],
) -> MatchResult:
    skill_matches, missing_skills = match_skills(
        candidate_skills,
        required_skills,
    )

    requirement_matches = []

    for requirement in requirements:
        requirement_matches.append(
            match_requirement(
                requirement_type=requirement["requirement_type"],
                requirement_text=requirement["text"],
                importance=requirement.get("importance"),
                required_skills=requirement.get("skills", []),
                candidate_skills=candidate_skills,
            )
        )

    skill_coverage = calculate_skill_coverage(
        candidate_skills,
        required_skills,
    )

    requirement_coverage = calculate_requirement_coverage(
        requirement_matches
    )

    gaps = [
        f"Missing skill: {skill}"
        for skill in missing_skills
    ]

    return MatchResult(
        skill_coverage=round(skill_coverage, 4),
        requirement_coverage=round(
            requirement_coverage,
            4,
        ),
        matched_skills=[
            match.skill_name
            for match in skill_matches
            if match.matched
        ],
        missing_skills=missing_skills,
        matched_requirements=requirement_matches,
        gaps=gaps,
    )


def build_candidate_semantic_text_from_snapshot(candidate) -> str:
    return build_candidate_semantic_text(
        headline=candidate.headline,
        summary=candidate.summary,
        target_roles=candidate.target_roles,
        skills=candidate.skills.keys(),
        experiences=[
            " ".join(str(value) for value in (
                item.get("role"), item.get("company"), item.get("description")
            ) if value)
            for item in candidate.experience
        ],
        projects=[
            " ".join(str(value) for value in (
                item.get("name"), item.get("description"), item.get("technologies")
            ) if value)
            for item in candidate.projects
        ],
        education=[
            " ".join(str(value) for value in (
                item.get("degree"), item.get("field_of_study"), item.get("institution")
            ) if value)
            for item in candidate.education
        ],
        certifications=[
            " ".join(str(value) for value in (
                item.get("name"), item.get("issuer"), item.get("description")
            ) if value)
            for item in candidate.certifications
        ],
    )


def build_job_semantic_text_from_snapshot(job) -> str:
    return build_job_semantic_text(
        title=job.title,
        company=job.company or "",
        description=job.description or "",
        location=job.location,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        requirements=[item.text for item in job.requirements],
    )


async def match_candidate_to_job_from_db(
    *,
    profile_id: UUID,
    job_id: UUID,
    session: AsyncSession,
    embedding_provider: EmbeddingProvider | None = None,
) -> MatchResult | None:
    candidate = await load_candidate_snapshot(
        profile_id,
        session,
    )

    if candidate is None:
        return None

    job = await load_job_snapshot(
        job_id,
        session,
    )

    if job is None:
        return None

    requirements = [
        {
            "requirement_type": requirement.requirement_type,
            "text": requirement.text,
            "importance": requirement.importance,
            "skills": requirement.skills,
        }
        for requirement in job.requirements
    ]

    result = match_candidate_to_job(
        candidate_skills=candidate.skills,
        required_skills=job.required_skills,
        requirements=requirements,
    )

    if embedding_provider is None:
        return result

    try:
        candidate_embedding = await get_or_create_embedding(
            entity_type="career_profile",
            entity_id=candidate.profile_id,
            source_text=build_candidate_semantic_text_from_snapshot(candidate),
            provider=embedding_provider,
            session=session,
        )
        job_embedding = await get_or_create_embedding(
            entity_type="job",
            entity_id=job.job_id,
            source_text=build_job_semantic_text_from_snapshot(job),
            provider=embedding_provider,
            session=session,
        )
    except EmbeddingError:
        return result

    result.semantic_similarity = calculate_semantic_similarity(
        candidate_embedding.embedding,
        job_embedding.embedding,
    )
    return result

async def rank_jobs_for_candidate(
    *,
    profile_id: UUID,
    session: AsyncSession,
    embedding_provider: EmbeddingProvider | None = None,
    location: str | None = None,
    search: str | None = None,
    limit: int = 20,
) -> list[tuple[JobSnapshot, MatchResult]] | None:
    """Rank active jobs for one candidate using the same match engine."""
    candidate = await load_candidate_snapshot(profile_id, session)
    if candidate is None:
        return None

    filters = [Job.is_active.is_(True)]
    if location:
        filters.append(Job.location.ilike(f"%{location}%"))
    if search:
        pattern = f"%{search}%"
        filters.append(
            Job.title.ilike(pattern)
            | Job.company.ilike(pattern)
            | Job.description.ilike(pattern)
        )

    result = await session.execute(
        select(Job)
        .options(
            selectinload(Job.requirements)
            .selectinload(JobRequirement.skills)
            .selectinload(JobRequirementSkill.skill)
        )
        .where(*filters)
        .order_by(Job.posted_at.desc().nullslast(), Job.created_at.desc())
        .limit(limit)
    )

    jobs = result.scalars().all()
    ranked: list[tuple[JobSnapshot, MatchResult]] = []

    candidate_text = build_candidate_semantic_text_from_snapshot(candidate)
    candidate_embedding = None
    if embedding_provider is not None:
        try:
            candidate_embedding = await get_or_create_embedding(
                entity_type="career_profile",
                entity_id=candidate.profile_id,
                source_text=candidate_text,
                provider=embedding_provider,
                session=session,
            )
        except EmbeddingError:
            candidate_embedding = None

    for job in jobs:
        requirements = []
        required_skills = []
        for requirement in job.requirements:
            skills = [item.skill.name for item in requirement.skills]
            required_skills.extend(skills)
            requirements.append({
                "requirement_type": requirement.requirement_type,
                "text": requirement.text,
                "importance": requirement.importance,
                "skills": skills,
            })

        snapshot = JobSnapshot(
            job_id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            application_url=job.application_url,
            requirements=[
                JobRequirementSnapshot(
                    requirement_id=item.id,
                    requirement_type=item.requirement_type,
                    text=item.text,
                    importance=item.importance if item.importance is not None else 0.5,
                    skills=[skill.skill.name for skill in item.skills],
                )
                for item in job.requirements
            ],
            required_skills=list(dict.fromkeys(required_skills)),
        )

        match = match_candidate_to_job(
            candidate_skills=candidate.skills,
            required_skills=snapshot.required_skills,
            requirements=requirements,
        )

        if candidate_embedding is not None:
            try:
                job_embedding = await get_or_create_embedding(
                    entity_type="job",
                    entity_id=snapshot.job_id,
                    source_text=build_job_semantic_text_from_snapshot(snapshot),
                    provider=embedding_provider,
                    session=session,
                )
                match.semantic_similarity = calculate_semantic_similarity(
                    candidate_embedding.embedding,
                    job_embedding.embedding,
                )
            except EmbeddingError:
                pass

        ranked.append((snapshot, match))

    ranked.sort(key=lambda item: item[1].score, reverse=True)
    return ranked

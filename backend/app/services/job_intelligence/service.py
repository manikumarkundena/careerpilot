import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.services.job_intelligence.classifier import classify_importance
from app.services.job_intelligence.extractor import (
    extract_requirements,
    extract_skills_from_text,
)
from app.services.job_intelligence.normalizer import load_skill_lookup
from app.services.job_intelligence.preprocessor import clean_job_description
from app.models.job_requirement_skill import JobRequirementSkill

async def analyze_job_description(
    text: str,
    session: AsyncSession,
) -> dict:
    """Analyze a raw job description without persisting it."""

    cleaned_text = clean_job_description(text)

    if not cleaned_text:
        return {
            "cleaned_text": "",
            "requirements": [],
            "skills": [],
        }

    requirements = extract_requirements(cleaned_text)
    skill_lookup = await load_skill_lookup(session)

    structured_requirements = []
    unique_skills: dict[str, dict[str, str]] = {}

    for requirement in requirements:
        requirement_type = requirement["requirement_type"]
        requirement_text = requirement["text"]

        extracted_skills = extract_skills_from_text(
            requirement_text,
            skill_lookup,
        )

        importance = classify_importance(
            requirement_text,
            requirement_type,
        )

        structured_requirements.append(
            {
                "requirement_type": requirement_type,
                "text": requirement_text,
                "skills": extracted_skills,
                "importance": importance,
            }
        )

        for skill in extracted_skills:
            unique_skills[skill["name"]] = skill

    return {
        "cleaned_text": cleaned_text,
        "requirements": structured_requirements,
        "skills": list(unique_skills.values()),
    }


async def analyze_and_persist_job(job_id, session):
    job = await session.get(Job, job_id)

    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    # Remove previous analysis for this job
    await session.execute(
        delete(JobRequirement).where(
            JobRequirement.job_id == job_id
        )
    )

    result = await analyze_job_description(
        job.description,
        session,
    )

    # Load skill catalog once
    skill_lookup = await load_skill_lookup(session)

    # Build canonical skill-name lookup
    canonical_skills = {}

    for skill in skill_lookup.values():
        canonical_skills[skill.name.lower()] = skill

    # Persist requirements
    for requirement in result["requirements"]:

        job_requirement = JobRequirement(
            job_id=job.id,
            requirement_type=requirement["requirement_type"],
            text=requirement["text"],
            importance=requirement["importance"],
            evidence=requirement["text"],
        )

        session.add(job_requirement)

        await session.flush()

        # Create requirement → skill links
        for skill_data in requirement["skills"]:

            skill = canonical_skills.get(
                skill_data["name"].lower()
            )

            if skill:
                session.add(
                    JobRequirementSkill(
                        requirement_id=job_requirement.id,
                        skill_id=skill.id,
                    )
                )

    await session.commit()

    return result
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.career_profile import CareerProfile
from app.models.skill import Skill


@dataclass(slots=True)
class CandidateSnapshot:
    profile_id: UUID
    headline: str | None
    summary: str | None
    target_roles: str | None

    skills: dict[str, str | None] = field(default_factory=dict)
    education: list[dict] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    certifications: list[dict] = field(default_factory=list)
    preferences: dict | None = None


async def load_candidate_snapshot(
    profile_id: UUID,
    session: AsyncSession,
) -> CandidateSnapshot | None:
    result = await session.execute(
        select(CareerProfile)
        .options(
            selectinload(CareerProfile.skills)
            .selectinload(Skill.skill),

            selectinload(CareerProfile.education),

            selectinload(CareerProfile.experience),

            selectinload(CareerProfile.projects),

            selectinload(CareerProfile.certifications),

            selectinload(CareerProfile.preferences),
        )
        .where(CareerProfile.id == profile_id)
    )

    profile = result.scalar_one_or_none()

    if profile is None:
        return None

    # -------------------------
    # Skills
    # -------------------------
    skills = {
        skill.skill.name: skill.proficiency
        for skill in profile.skills
    }

    # -------------------------
    # Education
    # -------------------------
    education = [
        {
            "institution": item.institution,
            "degree": item.degree,
            "field_of_study": item.field_of_study,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "grade": item.grade,
            "description": item.description,
        }
        for item in profile.education
    ]

    # -------------------------
    # Experience
    # -------------------------
    experience = [
        {
            "company": item.company,
            "role": item.role,
            "employment_type": item.employment_type,
            "location": item.location,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "description": item.description,
        }
        for item in profile.experience
    ]

    # -------------------------
    # Projects
    # -------------------------
    projects = [
        {
            "name": item.name,
            "description": item.description,
            "technologies": item.technologies,
            "project_url": item.project_url,
            "github_url": item.github_url,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "highlights": item.highlights,
        }
        for item in profile.projects
    ]

    # -------------------------
    # Certifications
    # -------------------------
    certifications = [
        {
            "name": item.name,
            "issuer": item.issuer,
            "issue_date": item.issue_date,
            "expiry_date": item.expiry_date,
            "credential_id": item.credential_id,
            "credential_url": item.credential_url,
            "description": item.description,
        }
        for item in profile.certifications
    ]

    # -------------------------
    # Preferences
    # -------------------------
    preferences = None

    if profile.preferences:
        preferences = {
            "target_roles": profile.preferences.target_roles,
            "preferred_locations": profile.preferences.preferred_locations,
            "remote_preference": profile.preferences.remote_preference,
            "employment_types": profile.preferences.employment_types,
            "minimum_salary": profile.preferences.minimum_salary,
            "currency": profile.preferences.currency,
            "willing_to_relocate": profile.preferences.willing_to_relocate,
            "preferred_experience_level": (
                profile.preferences.preferred_experience_level
            ),
        }

    # -------------------------
    # Final snapshot
    # -------------------------
    return CandidateSnapshot(
        profile_id=profile.id,
        headline=profile.headline,
        summary=profile.summary,
        target_roles=profile.target_roles,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        certifications=certifications,
        preferences=preferences,
    )
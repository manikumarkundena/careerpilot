from __future__ import annotations

from app.services.resume.jd_intelligence import extract_requirement_keywords
from app.services.resume.job_gap import analyze_job_requirements
from app.services.resume.optimizer import optimize_resume_for_job
from app.services.resume.schema import (
    ResumeDocument,
    ResumeEntry,
    ResumeSkill,
    ResumeSource,
    ResumeText,
)
from app.services.resume.profile_adapter import build_profile_content_candidates


def build_role_specific_resume(profile, job) -> tuple[ResumeDocument, object]:
    """Build a role-specific, provenance-aware resume from persisted facts.

    The job controls relevance and ordering; the profile remains the only
    source of candidate claims.
    """
    candidate_skills = [
        profile_skill.skill.name
        for profile_skill in profile.skills
        if profile_skill.skill is not None
    ]
    requirements = list(job.requirements)
    target_keywords = _extract_target_keywords(requirements)

    gap_analysis = analyze_job_requirements(requirements, set(candidate_skills))
    optimization = optimize_resume_for_job(
        candidates=build_profile_content_candidates(profile, set(candidate_skills)),
        candidate_skills=candidate_skills,
        target_keywords=target_keywords,
        gap_analysis=gap_analysis,
    )

    selected_skills = set(optimization.prioritized_skills)
    document = ResumeDocument(
        name=_text(
            profile,
            profile.user.display_name if profile.user else None,
            "profile",
            "display_name",
        ),
        headline=_text(profile, profile.headline, "profile", "headline"),
        summary=_text(profile, profile.summary, "profile", "summary"),
        skills=[
            ResumeSkill(
                name=profile_skill.skill.name,
                source=ResumeSource("skill", str(profile_skill.skill.id), "name"),
            )
            for profile_skill in profile.skills
            if profile_skill.skill is not None
            and skill_in_set(profile_skill.skill.name, selected_skills)
        ],
        experience=_build_experience(profile, optimization),
        projects=_build_projects(profile, optimization),
        education=_build_education(profile),
        certifications=_build_certifications(profile),
        achievements=_build_achievements(profile, optimization),
        links=_build_links(profile),
        metadata={
            "target_job_id": str(job.id),
            "target_role": job.title,
            "target_company": job.company,
            "keyword_coverage": str(gap_analysis.keyword_coverage),
            "must_have_coverage": str(gap_analysis.must_have_coverage),
            "preferred_coverage": str(gap_analysis.preferred_coverage),
        },
    )

    return document, gap_analysis


def _extract_target_keywords(requirements) -> set[str]:
    intelligence = extract_requirement_keywords(requirements)
    return {keyword.text for keyword in intelligence.keywords}


def _build_experience(profile, optimization):
    selected_ids = {
        item.source_id
        for item in optimization.selected_content
        if item.source_type == "experience"
    }
    return [
        ResumeEntry(
            title=item.role,
            organization=item.company,
            location=item.location,
            dates=_date_range(item.start_date, item.end_date),
            bullets=[
                ResumeText(
                    text=item.description,
                    source=ResumeSource("experience", str(item.id), "description"),
                )
            ]
            if item.description
            else [],
            source=ResumeSource("experience", str(item.id), "description"),
        )
        for item in profile.experience
        if str(item.id) in selected_ids
    ]


def _build_projects(profile, optimization):
    selected_ids = {
        item.source_id
        for item in optimization.selected_content
        if item.source_type == "project"
    }
    return [
        ResumeEntry(
            title=item.name,
            organization=None,
            location=None,
            dates=_date_range(item.start_date, item.end_date),
            bullets=[
                ResumeText(
                    text=item.description,
                    source=ResumeSource("project", str(item.id), "description"),
                )
            ]
            if item.description
            else [],
            source=ResumeSource("project", str(item.id), "description"),
        )
        for item in profile.projects
        if str(item.id) in selected_ids
    ]


def _build_achievements(profile, optimization):
    selected_ids = {
        item.source_id
        for item in optimization.selected_content
        if item.source_type == "achievement"
    }
    return [
        ResumeText(
            text=item.description or item.title,
            source=ResumeSource(
                "achievement",
                str(item.id),
                "description" if item.description else "title",
            ),
        )
        for item in profile.achievements
        if str(item.id) in selected_ids
    ]


def _build_links(profile):
    return [
        ResumeText(
            text=f"{item.label or item.platform}: {item.url}",
            source=ResumeSource("link", str(item.id), "url"),
        )
        for item in profile.links
    ]


def _build_education(profile):
    return [
        ResumeEntry(
            title=(
                f"{item.degree}{f' in {item.field_of_study}' if item.field_of_study else ''}"
                if item.degree
                else item.field_of_study or "Education"
            ),
            organization=item.institution,
            location=None,
            dates=_date_range(item.start_date, item.end_date),
            bullets=[
                ResumeText(
                    text=item.description,
                    source=ResumeSource("education", str(item.id), "description"),
                )
            ]
            if item.description
            else [],
            source=ResumeSource("education", str(item.id), "degree"),
        )
        for item in profile.education
    ]


def _build_certifications(profile):
    return [
        ResumeEntry(
            title=item.name,
            organization=item.issuer,
            location=None,
            dates=_date_range(item.issue_date, item.expiry_date),
            bullets=[
                ResumeText(
                    text=item.description,
                    source=ResumeSource("certification", str(item.id), "description"),
                )
            ]
            if item.description
            else [],
            source=ResumeSource("certification", str(item.id), "name"),
        )
        for item in profile.certifications
    ]


def _text(profile, value, source_type, field):
    if not value:
        return None
    return ResumeText(
        text=value,
        source=ResumeSource(source_type, str(profile.id), field),
    )


def _date_range(start, end):
    if start is None and end is None:
        return None
    if start is None:
        return end.isoformat()
    if end is None:
        return f"{start.isoformat()} – Present"
    return f"{start.isoformat()} – {end.isoformat()}"


def skill_in_set(skill: str, selected: set[str]) -> bool:
    normalized = {item.strip().lower() for item in selected}
    return skill.strip().lower() in normalized

from app.services.matching.models import RequirementMatch


def match_requirement(
    *,
    requirement_type: str,
    requirement_text: str,
    importance: float | None,
    required_skills: list[str],
    candidate_skills: dict[str, str | None],
) -> RequirementMatch:
    normalized_candidate = {
        skill.strip().lower()
        for skill in candidate_skills
    }

    matched_skills = [
        skill
        for skill in required_skills
        if skill.strip().lower() in normalized_candidate
    ]

    if required_skills:
        matched = len(matched_skills) > 0
    else:
        matched = False

    return RequirementMatch(
        requirement_text=requirement_text,
        requirement_type=requirement_type,
        importance=importance if importance is not None else 0.5,
        matched=matched,
        matched_skills=matched_skills,
    )
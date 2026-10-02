from app.services.matching.models import SkillMatch


def match_skills(
    candidate_skills: dict[str, str | None],
    required_skills: list[str],
) -> tuple[list[SkillMatch], list[str]]:
    normalized_candidate = {
        name.strip().lower(): proficiency
        for name, proficiency in candidate_skills.items()
    }

    matches: list[SkillMatch] = []
    missing: list[str] = []

    for skill in required_skills:
        normalized = skill.strip().lower()

        if normalized in normalized_candidate:
            matches.append(
                SkillMatch(
                    skill_name=skill,
                    matched=True,
                    proficiency=normalized_candidate[normalized],
                )
            )
        else:
            matches.append(
                SkillMatch(
                    skill_name=skill,
                    matched=False,
                )
            )
            missing.append(skill)

    return matches, missing
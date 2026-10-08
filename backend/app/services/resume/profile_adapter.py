from __future__ import annotations

import re

from app.services.resume.content_selector import ContentCandidate


def build_profile_content_candidates(
    profile,
    candidate_skill_names: set[str] | None = None,
) -> list[ContentCandidate]:
    """Convert persisted profile facts into selectable resume content.

    Known profile skills are matched as phrases so values such as
    "Spring Boot", "REST API", and "React.js" remain intact.
    """
    candidates: list[ContentCandidate] = []
    known_skills = tuple(
        sorted(
            (skill.strip() for skill in (candidate_skill_names or set()) if skill.strip()),
            key=len,
            reverse=True,
        )
    )

    for item in profile.experience:
        text = item.description or f"{item.role} at {item.company}"
        candidates.append(
            ContentCandidate(
                text=text,
                source_type="experience",
                source_id=str(item.id),
                keywords=tuple(_extract_keywords(text, known_skills)),
                priority=3.0,
            )
        )

    for item in profile.projects:
        text = item.description or item.name
        technology_keywords = _extract_keywords(
            item.technologies,
            known_skills,
        )
        candidates.append(
            ContentCandidate(
                text=text,
                source_type="project",
                source_id=str(item.id),
                keywords=tuple(
                    dict.fromkeys(
                        (*technology_keywords, *_extract_keywords(text, known_skills))
                    )
                ),
                priority=2.5,
            )
        )

    for item in profile.achievements:
        text = item.description or item.title
        candidates.append(
            ContentCandidate(
                text=text,
                source_type="achievement",
                source_id=str(item.id),
                keywords=tuple(_extract_keywords(text, known_skills)),
                priority=2.0,
            )
        )

    for item in profile.certifications:
        text = item.description or item.name
        candidates.append(
            ContentCandidate(
                text=text,
                source_type="certification",
                source_id=str(item.id),
                keywords=tuple(_extract_keywords(text, known_skills)),
                priority=1.5,
            )
        )

    return candidates


def _extract_keywords(
    value: str | None,
    known_skills: tuple[str, ...],
) -> list[str]:
    if not value:
        return []

    found: list[str] = []
    for skill in known_skills:
        if _contains_phrase(value, skill):
            found.append(skill)

    found.extend(_split_keywords(value))
    return list(dict.fromkeys(found))


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(phrase) + r"(?![A-Za-z0-9])"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def _split_keywords(value: str) -> list[str]:
    return [part.strip() for part in value.replace(",", " ").split() if part.strip()]

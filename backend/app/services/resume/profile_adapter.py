from __future__ import annotations

from app.services.resume.content_selector import ContentCandidate


def build_profile_content_candidates(profile) -> list[ContentCandidate]:
    """Convert persisted profile facts into selectable resume content.

    This adapter only reads user-provided facts. It does not generate,
    rewrite, or infer experience.
    """
    candidates: list[ContentCandidate] = []

    for item in profile.experience:
        candidates.append(
            ContentCandidate(
                text=item.description or f"{item.role} at {item.company}",
                source_type="experience",
                source_id=str(item.id),
                keywords=tuple(_split_keywords(item.description)),
                priority=3.0,
            )
        )

    for item in profile.projects:
        candidates.append(
            ContentCandidate(
                text=item.description or item.name,
                source_type="project",
                source_id=str(item.id),
                keywords=tuple(_split_keywords(item.technologies)),
                priority=2.5,
            )
        )

    for item in profile.certifications:
        candidates.append(
            ContentCandidate(
                text=item.description or item.name,
                source_type="certification",
                source_id=str(item.id),
                keywords=tuple(_split_keywords(item.description)),
                priority=1.5,
            )
        )

    return candidates


def _split_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace(",", " ").split() if part.strip()]

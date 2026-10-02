from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _section(title: str, values: Iterable[str]) -> str:
    cleaned = [_clean(value) for value in values if _clean(value)]
    if not cleaned:
        return ""
    return f"{title}: " + " | ".join(cleaned)


def build_candidate_semantic_text(
    *,
    headline: str | None = None,
    summary: str | None = None,
    target_roles: str | None = None,
    skills: Iterable[str] = (),
    experiences: Iterable[str] = (),
    projects: Iterable[str] = (),
    education: Iterable[str] = (),
    certifications: Iterable[str] = (),
) -> str:
    sections = [
        _section("Headline", [headline or ""]),
        _section("Summary", [summary or ""]),
        _section("Target roles", [target_roles or ""]),
        _section("Skills", skills),
        _section("Experience", experiences),
        _section("Projects", projects),
        _section("Education", education),
        _section("Certifications", certifications),
    ]
    return "\n".join(section for section in sections if section)


def build_job_semantic_text(
    *,
    title: str,
    company: str,
    description: str,
    location: str | None = None,
    employment_type: str | None = None,
    experience_level: str | None = None,
    requirements: Iterable[str] = (),
) -> str:
    sections = [
        _section("Title", [title]),
        _section("Company", [company]),
        _section("Location", [location or ""]),
        _section("Employment type", [employment_type or ""]),
        _section("Experience level", [experience_level or ""]),
        _section("Description", [description]),
        _section("Requirements", requirements),
    ]
    return "\n".join(section for section in sections if section)

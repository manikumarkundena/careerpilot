from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


SourceType = Literal[
    "profile",
    "experience",
    "project",
    "education",
    "certification",
    "achievement",
    "skill",
    "link",
]


@dataclass(slots=True, frozen=True)
class ResumeSource:
    source_type: SourceType
    source_id: str
    field: str


@dataclass(slots=True, frozen=True)
class ResumeText:
    text: str
    source: ResumeSource


@dataclass(slots=True)
class ResumeSkill:
    name: str
    source: ResumeSource


@dataclass(slots=True)
class ResumeEntry:
    title: str
    organization: str | None
    location: str | None
    dates: str | None
    bullets: list[ResumeText] = field(default_factory=list)
    source: ResumeSource | None = None


@dataclass(slots=True)
class ResumeDocument:
    """Canonical factual resume representation.

    Every user-facing text claim must carry a source reference. Renderers and
    AI optimizers operate on this representation rather than directly on ORM
    objects.
    """

    name: ResumeText | None = None
    headline: ResumeText | None = None
    summary: ResumeText | None = None
    skills: list[ResumeSkill] = field(default_factory=list)
    experience: list[ResumeEntry] = field(default_factory=list)
    projects: list[ResumeEntry] = field(default_factory=list)
    education: list[ResumeEntry] = field(default_factory=list)
    certifications: list[ResumeEntry] = field(default_factory=list)
    achievements: list[ResumeText] = field(default_factory=list)
    links: list[ResumeText] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

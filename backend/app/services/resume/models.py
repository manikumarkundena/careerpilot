from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ResumeBullet:
    text: str
    source_type: str
    source_id: str
    keywords: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ResumeSection:
    name: str
    bullets: tuple[ResumeBullet, ...] = ()


@dataclass(slots=True)
class ResumeDraft:
    target_job_id: str | None
    title: str
    summary: str | None
    skills: list[str] = field(default_factory=list)
    sections: list[ResumeSection] = field(default_factory=list)

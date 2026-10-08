from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from app.services.resume.ai_optimizer import (
    ResumeOptimizationProposal,
    ResumeOptimizationValidationError,
    validate_optimization_proposals,
)
from app.services.resume.schema import ResumeDocument, ResumeEntry, ResumeSkill, ResumeText


def apply_optimization_proposals(
    document: ResumeDocument,
    proposals: Iterable[ResumeOptimizationProposal],
) -> ResumeDocument:
    """Apply already-validated wording changes without changing provenance."""

    proposals = list(proposals)
    validate_optimization_proposals(document, proposals)

    replacements = {
        (
            proposal.source.source_type,
            proposal.source.source_id,
            proposal.source.field,
        ): proposal.proposed_text
        for proposal in proposals
    }

    def rewrite(item: ResumeText) -> ResumeText:
        key = (
            item.source.source_type,
            item.source.source_id,
            item.source.field,
        )
        text = replacements.get(key, item.text)
        return replace(item, text=text)

    return ResumeDocument(
        name=rewrite(document.name) if document.name else None,
        headline=rewrite(document.headline) if document.headline else None,
        summary=rewrite(document.summary) if document.summary else None,
        skills=[
            ResumeSkill(name=rewrite(ResumeText(skill.name, skill.source)).text, source=skill.source)
            for skill in document.skills
        ],
        experience=[_rewrite_entry(entry, rewrite) for entry in document.experience],
        projects=[_rewrite_entry(entry, rewrite) for entry in document.projects],
        education=[_rewrite_entry(entry, rewrite) for entry in document.education],
        certifications=[
            _rewrite_entry(entry, rewrite) for entry in document.certifications
        ],
        achievements=[rewrite(item) for item in document.achievements],
        links=[rewrite(item) for item in document.links],
        metadata=dict(document.metadata),
    )


def _rewrite_entry(
    entry: ResumeEntry,
    rewrite,
) -> ResumeEntry:
    return replace(
        entry,
        bullets=[rewrite(bullet) for bullet in entry.bullets],
    )

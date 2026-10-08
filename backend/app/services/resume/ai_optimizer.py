from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.resume.schema import ResumeDocument, ResumeSource


@dataclass(slots=True, frozen=True)
class ResumeOptimizationProposal:
    """A proposed rewrite tied to one verified resume source.

    The provider may improve wording, but it cannot introduce a proposal
    without identifying the exact source fact it is derived from.
    """

    source: ResumeSource
    original_text: str
    proposed_text: str
    rationale: str | None = None


class ResumeOptimizationProvider(Protocol):
    def propose(
        self,
        document: ResumeDocument,
        target_keywords: set[str],
    ) -> list[ResumeOptimizationProposal]:
        """Return source-backed wording proposals."""


class DeterministicResumeOptimizer:
    """Safe baseline provider used before connecting an external LLM.

    It intentionally makes no wording changes. This gives the pipeline a
    deterministic provider contract and a factuality-validation boundary
    without introducing model-dependent behavior into tests.
    """

    def propose(
        self,
        document: ResumeDocument,
        target_keywords: set[str],
    ) -> list[ResumeOptimizationProposal]:
        del target_keywords
        proposals: list[ResumeOptimizationProposal] = []

        for item in _iter_resume_text(document):
            proposals.append(
                ResumeOptimizationProposal(
                    source=item.source,
                    original_text=item.text,
                    proposed_text=item.text,
                    rationale="Deterministic baseline preserves the verified source text.",
                )
            )

        return proposals


class ResumeOptimizationValidationError(ValueError):
    """Raised when an optimization proposal cannot be tied to verified evidence."""


def validate_optimization_proposals(
    document: ResumeDocument,
    proposals: list[ResumeOptimizationProposal],
) -> None:
    """Validate the non-negotiable provenance boundary for optimizer output.

    A proposal is accepted only when its source exists in the verified
    ResumeDocument and the provider's original_text exactly matches that
    source text. This does not claim semantic truth of a rewritten sentence;
    it establishes the required evidence link that a future LLM provider must
    satisfy before its output can reach rendering.
    """

    source_texts = {
        (item.source.source_type, item.source.source_id, item.source.field): item.text
        for item in _iter_resume_text(document)
    }

    for index, proposal in enumerate(proposals):
        key = (
            proposal.source.source_type,
            proposal.source.source_id,
            proposal.source.field,
        )
        source_text = source_texts.get(key)

        if source_text is None:
            raise ResumeOptimizationValidationError(
                f"proposal[{index}] references unknown source: {key}"
            )

        if proposal.original_text != source_text:
            raise ResumeOptimizationValidationError(
                f"proposal[{index}] original_text does not match its verified source"
            )

        if not proposal.proposed_text.strip():
            raise ResumeOptimizationValidationError(
                f"proposal[{index}] proposed_text is empty"
            )


def _iter_resume_text(document: ResumeDocument):
    if document.name:
        yield document.name
    if document.headline:
        yield document.headline
    if document.summary:
        yield document.summary

    for skill in document.skills:
        yield _skill_as_text(skill)

    for entry in (
        *document.experience,
        *document.projects,
        *document.education,
        *document.certifications,
    ):
        for bullet in entry.bullets:
            yield bullet

    yield from document.achievements
    yield from document.links


def _skill_as_text(skill):
    from app.services.resume.schema import ResumeText

    return ResumeText(text=skill.name, source=skill.source)

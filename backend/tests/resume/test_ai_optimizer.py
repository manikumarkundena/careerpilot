import pytest

from app.services.resume.ai_optimizer import (
    DeterministicResumeOptimizer,
    ResumeOptimizationProposal,
    ResumeOptimizationValidationError,
    validate_optimization_proposals,
)
from app.services.resume.schema import ResumeDocument, ResumeEntry, ResumeSource, ResumeText


def _document() -> ResumeDocument:
    source = ResumeSource("project", "project-1", "description")
    return ResumeDocument(
        projects=[
            ResumeEntry(
                title="CareerPilot",
                organization=None,
                location=None,
                dates=None,
                bullets=[ResumeText("Built a FastAPI platform", source)],
                source=source,
            )
        ]
    )


def test_deterministic_optimizer_preserves_verified_source_text():
    document = _document()

    proposals = DeterministicResumeOptimizer().propose(
        document,
        {"FastAPI"},
    )

    assert len(proposals) == 1
    assert proposals[0].source.source_id == "project-1"
    assert proposals[0].original_text == "Built a FastAPI platform"
    assert proposals[0].proposed_text == proposals[0].original_text


def test_validator_accepts_source_backed_proposal():
    document = _document()
    proposal = ResumeOptimizationProposal(
        source=ResumeSource("project", "project-1", "description"),
        original_text="Built a FastAPI platform",
        proposed_text="Built a FastAPI platform for backend workflows",
    )

    validate_optimization_proposals(document, [proposal])


def test_validator_rejects_unknown_source():
    document = _document()
    proposal = ResumeOptimizationProposal(
        source=ResumeSource("project", "missing", "description"),
        original_text="Built a FastAPI platform",
        proposed_text="Built a FastAPI platform",
    )

    with pytest.raises(ResumeOptimizationValidationError, match="unknown source"):
        validate_optimization_proposals(document, [proposal])


def test_validator_rejects_source_text_mismatch():
    document = _document()
    proposal = ResumeOptimizationProposal(
        source=ResumeSource("project", "project-1", "description"),
        original_text="Built something else",
        proposed_text="Built a FastAPI platform",
    )

    with pytest.raises(
        ResumeOptimizationValidationError,
        match="original_text does not match",
    ):
        validate_optimization_proposals(document, [proposal])


def test_validator_rejects_empty_proposal():
    document = _document()
    proposal = ResumeOptimizationProposal(
        source=ResumeSource("project", "project-1", "description"),
        original_text="Built a FastAPI platform",
        proposed_text="   ",
    )

    with pytest.raises(
        ResumeOptimizationValidationError,
        match="proposed_text is empty",
    ):
        validate_optimization_proposals(document, [proposal])

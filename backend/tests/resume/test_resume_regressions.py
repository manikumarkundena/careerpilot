import pytest

from app.services.resume.ai_optimizer import (
    ResumeOptimizationProposal,
    ResumeOptimizationValidationError,
)
from app.services.resume.applier import apply_optimization_proposals
from app.services.resume.schema import ResumeDocument, ResumeEntry, ResumeSource, ResumeText
from app.services.resume.validator import validate_resume_document


def _document() -> ResumeDocument:
    source = ResumeSource("project", "project-1", "description")
    return ResumeDocument(
        name=ResumeText("Candidate", ResumeSource("profile", "user-1", "name")),
        skills=[],
        projects=[
            ResumeEntry(
                title="CareerPilot",
                organization=None,
                location=None,
                dates=None,
                bullets=[ResumeText("Built a FastAPI platform", source)],
                source=source,
            )
        ],
    )


def test_applying_proposal_preserves_source_and_does_not_mutate_original():
    document = _document()
    proposal = ResumeOptimizationProposal(
        source=ResumeSource("project", "project-1", "description"),
        original_text="Built a FastAPI platform",
        proposed_text="Built a FastAPI platform for career management",
    )

    optimized = apply_optimization_proposals(document, [proposal])

    assert document.projects[0].bullets[0].text == "Built a FastAPI platform"
    assert optimized.projects[0].bullets[0].text == (
        "Built a FastAPI platform for career management"
    )
    assert optimized.projects[0].bullets[0].source == document.projects[0].bullets[0].source


def test_applying_proposal_rejects_unknown_source_before_rewriting():
    document = _document()
    proposal = ResumeOptimizationProposal(
        source=ResumeSource("project", "not-in-profile", "description"),
        original_text="Built a FastAPI platform",
        proposed_text="Built a Kubernetes platform",
    )

    with pytest.raises(ResumeOptimizationValidationError, match="unknown source"):
        apply_optimization_proposals(document, [proposal])

    assert document.projects[0].bullets[0].text == "Built a FastAPI platform"


def test_resume_document_validator_rejects_blank_candidate_name():
    document = _document()
    document.name = ResumeText("", ResumeSource("profile", "user-1", "name"))

    issues = validate_resume_document(document)

    assert any(issue.code == "empty_text" for issue in issues)

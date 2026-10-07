from __future__ import annotations

from dataclasses import dataclass

from app.services.resume.artifact import PdfArtifactReport, validate_pdf_artifact
from app.services.resume.builder import build_role_specific_resume
from app.services.resume.latex import render_resume_latex
from app.services.resume.pdf import compile_latex_to_pdf
from app.services.resume.quality import ResumeQualityReport, evaluate_resume_quality
from app.services.resume.schema import ResumeDocument
from app.services.resume.validator import ResumeValidationIssue, validate_resume_document


@dataclass(slots=True, frozen=True)
class ResumeGenerationResult:
    document: ResumeDocument
    quality: ResumeQualityReport
    artifact: PdfArtifactReport
    pdf_bytes: bytes


def generate_resume_pdf(profile, job) -> ResumeGenerationResult:
    """Run the complete factual resume generation pipeline.

    The profile is the sole source of candidate claims. The job only controls
    relevance and ordering.
    """
    document, gap_analysis = build_role_specific_resume(profile, job)

    validation_issues = validate_resume_document(document)
    if validation_issues:
        raise ResumeGenerationValidationError(validation_issues)

    quality = evaluate_resume_quality(document, gap_analysis)
    if not quality.passed:
        raise ResumeGenerationQualityError(quality)

    latex_source = render_resume_latex(document)
    pdf_bytes = compile_latex_to_pdf(latex_source)

    expected_text = _expected_pdf_text(document)
    artifact = validate_pdf_artifact(pdf_bytes, expected_text)
    if not artifact.passed:
        raise ResumeGenerationArtifactError(artifact)

    return ResumeGenerationResult(
        document=document,
        quality=quality,
        artifact=artifact,
        pdf_bytes=pdf_bytes,
    )


class ResumeGenerationValidationError(RuntimeError):
    def __init__(self, issues: list[ResumeValidationIssue]) -> None:
        super().__init__("Generated resume failed validation")
        self.issues = issues


class ResumeGenerationQualityError(RuntimeError):
    def __init__(self, report: ResumeQualityReport) -> None:
        super().__init__("Generated resume failed quality checks")
        self.report = report


class ResumeGenerationArtifactError(RuntimeError):
    def __init__(self, report: PdfArtifactReport) -> None:
        super().__init__("Generated PDF failed artifact validation")
        self.report = report


def _expected_pdf_text(document: ResumeDocument) -> list[str]:
    expected: list[str] = []

    if document.name:
        expected.append(document.name.text)

    if document.headline:
        expected.append(document.headline.text)

    expected.extend(skill.name for skill in document.skills)

    for entry in (
        *document.experience,
        *document.projects,
        *document.education,
        *document.certifications,
    ):
        expected.append(entry.title)

    return expected

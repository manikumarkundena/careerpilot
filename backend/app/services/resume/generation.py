from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.services.resume.ai_optimizer import (
    ResumeOptimizationProvider,
    ResumeOptimizationValidationError,
)
from app.services.resume.applier import apply_optimization_proposals
from app.services.resume.artifact import PdfArtifactReport, validate_pdf_artifact
from app.services.resume.builder import build_role_specific_resume
from app.services.resume.latex import render_resume_latex
from app.services.resume.llm_optimizer import LLMOptimizerConfig, LLMResumeOptimizer
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
    ai_optimized: bool = False


def generate_resume_pdf(
    profile,
    job,
    *,
    optimize_with_ai: bool = False,
    optimizer: ResumeOptimizationProvider | None = None,
) -> ResumeGenerationResult:
    """Generate a resume, optionally applying validated AI wording proposals."""

    document, gap_analysis = build_role_specific_resume(profile, job)

    if optimize_with_ai:
        if optimizer is None:
            optimizer = _build_configured_optimizer()
        target_keywords = {
            requirement.text
            for requirement in getattr(job, "requirements", ())
            if getattr(requirement, "text", None)
        }
        proposals = optimizer.propose(document, target_keywords)
        document = apply_optimization_proposals(document, proposals)

    validation_issues = validate_resume_document(document)
    if validation_issues:
        raise ResumeGenerationValidationError(validation_issues)

    quality = evaluate_resume_quality(document, gap_analysis)
    if not quality.passed:
        raise ResumeGenerationQualityError(quality)

    latex_source = render_resume_latex(document)
    pdf_bytes = compile_latex_to_pdf(latex_source)

    artifact = validate_pdf_artifact(pdf_bytes, _expected_pdf_text(document))
    if not artifact.passed:
        raise ResumeGenerationArtifactError(artifact)

    return ResumeGenerationResult(
        document=document,
        quality=quality,
        artifact=artifact,
        pdf_bytes=pdf_bytes,
        ai_optimized=optimize_with_ai,
    )


def _build_configured_optimizer() -> ResumeOptimizationProvider:
    if not settings.resume_llm_api_url or not settings.resume_llm_api_key:
        raise ResumeOptimizationConfigurationError(
            "AI resume optimization is enabled but no LLM endpoint/API key is configured"
        )

    return LLMResumeOptimizer(
        LLMOptimizerConfig(
            endpoint=settings.resume_llm_api_url,
            api_key=settings.resume_llm_api_key,
            model=settings.resume_llm_model,
            timeout_seconds=settings.resume_llm_timeout_seconds,
        ),
        request=_request_llm,
    )


def _request_llm(
    endpoint: str,
    payload: dict,
    headers: dict,
    timeout: float,
) -> str:
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            **headers,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except TimeoutError as exc:
        raise ResumeOptimizationTimeoutError() from exc
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise ResumeOptimizationTimeoutError() from exc
        raise ResumeOptimizationProviderError() from exc
    except OSError as exc:
        raise ResumeOptimizationProviderError() from exc

    try:
        body = json.loads(raw_body)
        content = body["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise ResumeOptimizationProviderError() from exc

    if not isinstance(content, str) or not content.strip():
        raise ResumeOptimizationProviderError()
    return content


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


class ResumeOptimizationConfigurationError(RuntimeError):
    pass


class ResumeOptimizationProviderError(RuntimeError):
    """External AI provider failed or returned an unusable completion."""


class ResumeOptimizationTimeoutError(ResumeOptimizationProviderError):
    """External AI provider did not respond before its configured timeout."""


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

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.resume.job_gap import ResumeGapAnalysis
from app.services.resume.schema import ResumeDocument


@dataclass(slots=True, frozen=True)
class ResumeQualityIssue:
    code: str
    severity: str
    message: str


@dataclass(slots=True)
class ResumeQualityReport:
    keyword_coverage: float
    required_skills_covered: int
    required_skills_total: int
    must_have_coverage: float = 1.0
    preferred_coverage: float = 1.0
    sections_present: tuple[str, ...] = ()
    issues: list[ResumeQualityIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


def evaluate_resume_quality(
    document: ResumeDocument,
    gap_analysis: ResumeGapAnalysis,
    *,
    max_experience_entries: int = 6,
    max_project_entries: int = 5,
) -> ResumeQualityReport:
    """Evaluate resume structure and job alignment without fabricating an ATS score."""
    sections: list[str] = []
    issues: list[ResumeQualityIssue] = []

    if document.name and document.name.text.strip():
        sections.append("name")
    else:
        issues.append(
            ResumeQualityIssue("missing_name", "error", "Resume has no candidate name.")
        )

    if document.headline and document.headline.text.strip():
        sections.append("headline")

    if document.summary and document.summary.text.strip():
        sections.append("summary")

    if document.skills:
        sections.append("skills")
    else:
        issues.append(
            ResumeQualityIssue("missing_skills", "error", "Resume contains no skills.")
        )

    if document.experience:
        sections.append("experience")
    if document.projects:
        sections.append("projects")
    if document.education:
        sections.append("education")
    if document.certifications:
        sections.append("certifications")

    if len(document.experience) > max_experience_entries:
        issues.append(
            ResumeQualityIssue(
                "experience_over_limit",
                "warning",
                f"Resume contains {len(document.experience)} experience entries; "
                f"target maximum is {max_experience_entries}.",
            )
        )

    if len(document.projects) > max_project_entries:
        issues.append(
            ResumeQualityIssue(
                "projects_over_limit",
                "warning",
                f"Resume contains {len(document.projects)} project entries; "
                f"target maximum is {max_project_entries}.",
            )
        )

    if not document.experience and not document.projects:
        issues.append(
            ResumeQualityIssue(
                "missing_evidence",
                "warning",
                "Resume has no experience or project evidence.",
            )
        )

    if gap_analysis.keyword_coverage < 0.5:
        issues.append(
            ResumeQualityIssue(
                "low_keyword_coverage",
                "warning",
                "Less than half of extracted required skills are covered.",
            )
        )

    return ResumeQualityReport(
        keyword_coverage=gap_analysis.keyword_coverage,
        required_skills_covered=len(gap_analysis.matched_requirements),
        required_skills_total=(
            len(gap_analysis.matched_requirements) + len(gap_analysis.gaps)
        ),
        must_have_coverage=gap_analysis.must_have_coverage,
        preferred_coverage=gap_analysis.preferred_coverage,
        sections_present=tuple(sections),
        issues=issues,
    )

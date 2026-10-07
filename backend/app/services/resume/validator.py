from __future__ import annotations

from dataclasses import dataclass

from app.services.resume.schema import ResumeDocument, ResumeEntry, ResumeText


@dataclass(slots=True, frozen=True)
class ResumeValidationIssue:
    code: str
    message: str
    source: str | None = None


def validate_resume_document(document: ResumeDocument) -> list[ResumeValidationIssue]:
    """Validate provenance and basic structural safety before rendering."""
    issues: list[ResumeValidationIssue] = []

    text_fields = [
        ("name", document.name),
        ("headline", document.headline),
        ("summary", document.summary),
        *[(f"achievement[{i}]", item) for i, item in enumerate(document.achievements)],
        *[(f"link[{i}]", item) for i, item in enumerate(document.links)],
    ]

    for label, item in text_fields:
        if item is not None:
            _validate_text(issues, label, item)

    for section_name, entries in (
        ("experience", document.experience),
        ("projects", document.projects),
        ("education", document.education),
        ("certifications", document.certifications),
    ):
        for index, entry in enumerate(entries):
            _validate_entry(issues, f"{section_name}[{index}]", entry)

    for index, skill in enumerate(document.skills):
        if not skill.name.strip():
            issues.append(
                ResumeValidationIssue(
                    code="empty_skill",
                    message=f"{section_name_or_skill(document, index)} is empty",
                )
            )
        if not skill.source.source_id:
            issues.append(
                ResumeValidationIssue(
                    code="missing_provenance",
                    message=f"skills[{index}] has no source id",
                )
            )

    return issues


def _validate_text(
    issues: list[ResumeValidationIssue],
    label: str,
    item: ResumeText,
) -> None:
    if not item.text.strip():
        issues.append(
            ResumeValidationIssue(
                code="empty_text",
                message=f"{label} is empty",
            )
        )
    if not item.source.source_id:
        issues.append(
            ResumeValidationIssue(
                code="missing_provenance",
                message=f"{label} has no source id",
            )
        )


def _validate_entry(
    issues: list[ResumeValidationIssue],
    label: str,
    entry: ResumeEntry,
) -> None:
    if not entry.title.strip():
        issues.append(
            ResumeValidationIssue(
                code="empty_entry_title",
                message=f"{label} has an empty title",
            )
        )
    if entry.source is not None and not entry.source.source_id:
        issues.append(
            ResumeValidationIssue(
                code="missing_provenance",
                message=f"{label} has no source id",
            )
        )
    for index, bullet in enumerate(entry.bullets):
        _validate_text(issues, f"{label}.bullets[{index}]", bullet)


def section_name_or_skill(document: ResumeDocument, index: int) -> str:
    return f"skills[{index}]"

from app.services.resume.schema import (
    ResumeDocument,
    ResumeSkill,
    ResumeSource,
    ResumeText,
)
from app.services.resume.validator import validate_resume_document


def source(source_type="profile", source_id="profile-1", field="summary"):
    return ResumeSource(source_type=source_type, source_id=source_id, field=field)


def test_valid_resume_document_has_no_provenance_issues():
    document = ResumeDocument(
        headline=ResumeText("Backend Developer", source()),
        summary=ResumeText("Builds APIs.", source()),
        skills=[
            ResumeSkill("FastAPI", source("skill", "skill-1", "name")),
        ],
    )

    assert validate_resume_document(document) == []


def test_missing_provenance_is_rejected():
    document = ResumeDocument(
        summary=ResumeText(
            "Unsupported claim",
            ResumeSource("profile", "", "summary"),
        )
    )

    issues = validate_resume_document(document)

    assert any(issue.code == "missing_provenance" for issue in issues)


def test_empty_text_is_rejected():
    document = ResumeDocument(
        summary=ResumeText("", source()),
    )

    issues = validate_resume_document(document)

    assert any(issue.code == "empty_text" for issue in issues)

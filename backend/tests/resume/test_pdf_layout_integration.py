"""Real-tool regression test for the standard-to-compact PDF layout retry.

Requires pdflatex, enumitem (texlive-latex-extra), pdftotext, and pdfinfo.
"""
import shutil

import pytest

from app.services.resume.artifact import validate_pdf_artifact
from app.services.resume.latex import render_resume_latex
from app.services.resume.pdf import compile_latex_to_pdf
from app.services.resume.schema import ResumeDocument, ResumeEntry, ResumeSource, ResumeText


_REQUIRED_TOOLS = ("pdflatex", "pdftotext", "pdfinfo")


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in _REQUIRED_TOOLS),
    reason="real PDF layout integration test requires LaTeX and Poppler tools",
)
def test_compact_layout_rescues_real_multipage_resume_without_losing_content():
    source = ResumeSource("project", "integration-fixture", "description")
    achievement_source = ResumeSource("achievement", "integration-fixture", "achievement")
    bullet_text = (
        "Designed and developed REST APIs, integrated PostgreSQL databases, "
        "implemented secure authentication, input validation, error handling, "
        "automated unit testing, deployment workflows, and maintainable "
        "backend architecture."
    )
    document = ResumeDocument(
        name=ResumeText("Candidate Integration", ResumeSource("profile", "fixture", "name")),
        headline=ResumeText("Backend Software Engineer", ResumeSource("profile", "fixture", "headline")),
        achievements=[
            ResumeText(
                f"Demonstrated measurable engineering delivery and cross-functional execution "
                f"across portfolio initiative {index:02d}.",
                achievement_source,
            )
            for index in range(1, 13)
        ],
        projects=[
            ResumeEntry(
                title=f"Backend Project {index}",
                organization="Engineering Portfolio",
                location=None,
                dates="2025–2026",
                bullets=[
                    ResumeText(bullet_text, source),
                    ResumeText(bullet_text, source),
                    ResumeText(bullet_text, source),
                ],
                source=source,
            )
            for index in range(1, 9)
        ],
    )
    expected = [
        "Candidate Integration",
        "Backend Software Engineer",
        *(f"Backend Project {index}" for index in range(1, 9)),
        "maintainable backend architecture",
        "portfolio initiative 12",
    ]

    standard_pdf = compile_latex_to_pdf(render_resume_latex(document))
    standard_report = validate_pdf_artifact(standard_pdf, expected)

    # The standard PDF must be structurally valid and retain all expected text;
    # only its page-count gate should cause rejection.
    assert standard_report.valid_pdf_signature
    assert standard_report.byte_size > 100
    assert standard_report.extractable_text.strip()
    assert standard_report.missing_expected_text == ()
    assert standard_report.page_count is not None
    assert standard_report.page_count > 1
    assert not standard_report.passed

    compact_pdf = compile_latex_to_pdf(render_resume_latex(document, compact=True))
    compact_report = validate_pdf_artifact(compact_pdf, expected)

    assert compact_report.page_count == 1
    assert compact_report.passed
    assert compact_report.missing_expected_text == ()

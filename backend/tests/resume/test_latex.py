from app.services.resume.latex import escape_latex, render_resume_latex
from app.services.resume.schema import ResumeDocument, ResumeSource, ResumeText


def test_escape_latex_handles_user_controlled_characters():
    escaped = escape_latex(r"C++ & 100%_ready #1")

    assert r"\&" in escaped
    assert r"\%" in escaped
    assert r"\_" in escaped
    assert r"\#" in escaped


def test_render_resume_latex_is_single_column_and_text_first():
    document = ResumeDocument(
        name=ResumeText(
            "Candidate & Developer",
            ResumeSource("profile", "p1", "display_name"),
        ),
        summary=ResumeText(
            "Backend developer",
            ResumeSource("profile", "p1", "summary"),
        ),
    )

    latex = render_resume_latex(document)

    assert r"\documentclass[10pt]{article}" in latex
    assert r"\section*{Summary}" in latex
    assert "Candidate \\& Developer" in latex
    assert r"\begin{tabular" not in latex
    assert r"\begin{multicols" not in latex



def test_compact_resume_latex_uses_tighter_layout():
    document = ResumeDocument(
        name=ResumeText(
            "Candidate",
            ResumeSource("profile", "p1", "display_name"),
        ),
        summary=ResumeText(
            "Backend developer",
            ResumeSource("profile", "p1", "summary"),
        ),
    )

    standard = render_resume_latex(document)
    compact = render_resume_latex(document, compact=True)

    assert standard != compact
    assert r"\footnotesize" in compact
    assert "top=0.32in,bottom=0.32in" in compact
    assert r"\setlength{\parskip}{0pt}" in compact
    assert r"\@startsection{section}{1}{\z@}{3pt}{1pt}" in compact
    assert "Candidate" in compact
    assert "Backend developer" in compact

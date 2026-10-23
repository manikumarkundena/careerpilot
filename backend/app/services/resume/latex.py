from __future__ import annotations

from app.services.resume.schema import ResumeDocument, ResumeEntry


_LATEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(value: str) -> str:
    """Escape user-controlled text before inserting it into LaTeX."""
    return "".join(_LATEX_REPLACEMENTS.get(char, char) for char in value)


def render_resume_latex(document: ResumeDocument) -> str:
    """Render a compact, single-column, text-first resume for ATS parsing.

    The template prioritizes conventional headings, selectable PDF text,
    consistent spacing, and readable density. Page count still depends on
    the amount of source content; generation must validate the compiled PDF.
    """
    sections: list[str] = []

    if document.name:
        sections.append(
            f"\\begin{{center}}\\textbf{{\\LARGE "
            f"{escape_latex(document.name.text)}}}\\end{{center}}"
        )

    if document.headline:
        sections.append(
            f"\\begin{{center}}{escape_latex(document.headline.text)}"
            f"\\end{{center}}"
        )

    if document.links:
        sections.append(
            r"\begin{center}\footnotesize "
            + r"\quad | \quad ".join(escape_latex(item.text) for item in document.links)
            + r"\end{center}"
        )

    if document.summary:
        sections.extend([
            r"\section*{Summary}",
            escape_latex(document.summary.text),
        ])

    if document.skills:
        sections.extend([
            r"\section*{Technical Skills}",
            escape_latex(", ".join(skill.name for skill in document.skills)),
        ])

    _append_entries(sections, "Experience", document.experience)
    _append_entries(sections, "Projects", document.projects)
    _append_entries(sections, "Education", document.education)
    _append_entries(sections, "Certifications", document.certifications)

    if document.achievements:
        sections.append(r"\section*{Achievements}")
        sections.append(r"\begin{itemize}")
        sections.extend(
            f"\\item {escape_latex(item.text)}"
            for item in document.achievements
        )
        sections.append(r"\end{itemize}")

    body = "\n\n".join(sections)
    return f"""\\documentclass[10pt]{{article}}
\\usepackage[margin=0.55in,top=0.48in,bottom=0.48in]{{geometry}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\usepackage{{titlesec}}
\\pagestyle{{empty}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{2pt}}
\\setlist[itemize]{{leftmargin=*,nosep,topsep=2pt,parsep=0pt,partopsep=0pt}}
\\titlespacing*{{\\section}}{{0pt}}{{5pt}}{{2pt}}
\\titleformat{{\\section}}{{\\normalsize\\bfseries}}{{}}{{0pt}}{{}}
\\emergencystretch=2em
\\begin{{document}}
\\small

{body}

\\end{{document}}
"""


def _append_entries(
    sections: list[str],
    heading: str,
    entries: list[ResumeEntry],
) -> None:
    if not entries:
        return

    sections.append(f"\\section*{{{heading}}}")
    for entry in entries:
        title = escape_latex(entry.title)
        organization = escape_latex(entry.organization) if entry.organization else ""
        dates = escape_latex(entry.dates) if entry.dates else ""
        location = escape_latex(entry.location) if entry.location else ""

        metadata = " | ".join(
            part for part in (organization, location, dates) if part
        )
        sections.append(f"\\textbf{{{title}}}")
        if metadata:
            sections.append(f"\\hfill {{\\footnotesize {metadata}}}")

        if entry.bullets:
            sections.append(r"\begin{itemize}")
            sections.extend(
                f"\\item {escape_latex(bullet.text)}"
                for bullet in entry.bullets
            )
            sections.append(r"\end{itemize}")

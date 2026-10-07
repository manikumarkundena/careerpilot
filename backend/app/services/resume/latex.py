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
    """Render an ATS-oriented, single-column LaTeX resume."""
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

    if document.summary:
        sections.extend([
            r"\section*{Summary}",
            escape_latex(document.summary.text),
        ])

    if document.skills:
        sections.extend([
            r"\section*{Skills}",
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

    if document.links:
        sections.append(r"\section*{Links}")
        sections.extend(escape_latex(item.text) for item in document.links)

    body = "\n\n".join(sections)
    return f"""\\documentclass[10pt]{{article}}
\\usepackage[margin=0.65in]{{geometry}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\setlist[itemize]{{leftmargin=*,nosep}}
\\pagestyle{{empty}}
\\setlength{{\\parindent}}{{0pt}}
\\begin{{document}}

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

        metadata = " | ".join(
            part for part in (organization, entry.location, dates) if part
        )
        sections.append(f"\\textbf{{{title}}}")
        if metadata:
            sections.append(f"\\hfill {escape_latex(metadata)}")

        if entry.bullets:
            sections.append(r"\begin{itemize}")
            sections.extend(
                f"\\item {escape_latex(bullet.text)}"
                for bullet in entry.bullets
            )
            sections.append(r"\end{itemize}")

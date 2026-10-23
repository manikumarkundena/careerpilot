from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApplicationEmailDraft:
    subject: str
    body: str
    suggested_attachment: str = "Role-specific resume PDF"


def build_application_email_draft(
    *,
    candidate_name: str,
    role: str,
    company: str,
    skills: list[str],
    projects: list[str],
    institution: str | None = None,
) -> ApplicationEmailDraft:
    """Build a concise, evidence-based application email without inflated claims."""
    name = candidate_name.strip() or "Candidate"
    role = role.strip()
    company = company.strip()
    paragraphs = [
        "Dear Hiring Team,",
        f"I am writing to apply for the {role} position at {company}.",
    ]

    evidence = []
    if institution and institution.strip():
        evidence.append(f"I am studying at {institution.strip()}")
    clean_skills = [item.strip() for item in skills if item and item.strip()]
    if clean_skills:
        evidence.append("My relevant skills include " + ", ".join(clean_skills[:4]))
    clean_projects = [item.strip() for item in projects if item and item.strip()]
    if clean_projects:
        evidence.append("My project work includes " + ", ".join(clean_projects[:2]))
    if evidence:
        paragraphs.append(". ".join(evidence) + ".")

    paragraphs.extend([
        "I would appreciate your consideration. I have included my resume for review and would be glad to provide any additional information that would be useful.",
        "Thank you for your time.\n\nRegards,\n" + name,
    ])
    return ApplicationEmailDraft(
        subject=f"Application for {role} — {name}",
        body="\n\n".join(paragraphs),
    )

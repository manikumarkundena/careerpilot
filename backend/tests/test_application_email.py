from app.services.application_email import build_application_email_draft


def test_application_email_is_concise_and_avoids_inflated_claims():
    draft = build_application_email_draft(
        candidate_name="Manikumar Kundena",
        role="Backend Engineering Intern",
        company="Example Systems",
        skills=["Python", "FastAPI", "PostgreSQL"],
        projects=["CareerPilot"],
        institution="Siddaganga Institute of Technology",
    )

    assert draft.subject == "Application for Backend Engineering Intern — Manikumar Kundena"
    assert "Dear Hiring Team," in draft.body
    assert "I am writing to apply" in draft.body
    assert "Python, FastAPI, PostgreSQL" in draft.body
    assert "CareerPilot" in draft.body
    assert "Siddaganga Institute of Technology" in draft.body
    assert "best candidate" not in draft.body.lower()
    assert "revolutionary" not in draft.body.lower()
    assert "Regards,\nManikumar Kundena" in draft.body


def test_application_email_works_without_optional_evidence():
    draft = build_application_email_draft(
        candidate_name="Candidate",
        role="Software Intern",
        company="Example",
        skills=[],
        projects=[],
    )

    assert "I am writing to apply for the Software Intern position at Example." in draft.body
    assert draft.suggested_attachment == "Role-specific resume PDF"

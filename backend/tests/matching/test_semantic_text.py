from app.services.matching.semantic_text import (
    build_candidate_semantic_text,
    build_job_semantic_text,
)


def test_candidate_semantic_text_is_structured_and_deterministic():
    text = build_candidate_semantic_text(
        headline="Backend Developer",
        summary="Builds APIs and data systems.",
        target_roles="Backend Engineer",
        skills=["Python", "PostgreSQL"],
        experiences=["Built FastAPI services"],
        projects=["CareerPilot - AI career platform"],
    )

    assert text == (
        "Headline: Backend Developer\n"
        "Summary: Builds APIs and data systems.\n"
        "Target roles: Backend Engineer\n"
        "Skills: Python | PostgreSQL\n"
        "Experience: Built FastAPI services\n"
        "Projects: CareerPilot - AI career platform"
    )


def test_job_semantic_text_contains_context_and_requirements():
    text = build_job_semantic_text(
        title="Software Engineer",
        company="Example",
        description="Build backend services.",
        location="Bengaluru",
        experience_level="Entry level",
        requirements=["Python", "REST APIs"],
    )

    assert "Title: Software Engineer" in text
    assert "Company: Example" in text
    assert "Location: Bengaluru" in text
    assert "Experience level: Entry level" in text
    assert "Requirements: Python | REST APIs" in text

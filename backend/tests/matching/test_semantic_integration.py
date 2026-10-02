from types import SimpleNamespace

from app.services.matching.service import (
    build_candidate_semantic_text_from_snapshot,
    build_job_semantic_text_from_snapshot,
)


def test_candidate_semantic_snapshot_builder():
    candidate = SimpleNamespace(
        headline="Backend Engineer",
        summary="Builds APIs",
        target_roles="Backend Developer",
        skills={"Python": "Advanced", "FastAPI": "Intermediate"},
        experience=[{"role": "Developer", "company": "Acme", "description": "APIs"}],
        projects=[{"name": "CareerPilot", "description": "AI platform", "technologies": "FastAPI"}],
        education=[],
        certifications=[],
    )
    text = build_candidate_semantic_text_from_snapshot(candidate)
    assert "Headline: Backend Engineer" in text
    assert "Skills: Python | FastAPI" in text
    assert "Experience: Developer Acme APIs" in text


def test_job_semantic_snapshot_builder():
    job = SimpleNamespace(
        title="Backend Engineer",
        company="Acme",
        description="Build APIs",
        location="Bengaluru",
        employment_type="Internship",
        experience_level="Entry level",
        requirements=[SimpleNamespace(text="Python and FastAPI")],
    )
    text = build_job_semantic_text_from_snapshot(job)
    assert "Title: Backend Engineer" in text
    assert "Company: Acme" in text
    assert "Requirements: Python and FastAPI" in text

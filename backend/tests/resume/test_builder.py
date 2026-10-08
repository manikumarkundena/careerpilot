from types import SimpleNamespace
from uuid import uuid4

from app.services.resume.builder import build_role_specific_resume
from app.services.resume.validator import validate_resume_document


def test_builder_creates_role_specific_resume_from_profile_facts():
    fastapi = SimpleNamespace(id=uuid4(), name="FastAPI")
    postgres = SimpleNamespace(id=uuid4(), name="PostgreSQL")
    profile = SimpleNamespace(
        id=uuid4(),
        user=SimpleNamespace(display_name="Candidate"),
        headline="Backend Developer",
        summary="Builds backend systems.",
        skills=[
            SimpleNamespace(skill=fastapi),
            SimpleNamespace(skill=postgres),
        ],
        experience=[
            SimpleNamespace(
                id=uuid4(),
                role="Backend Intern",
                company="Acme",
                location="Remote",
                start_date=None,
                end_date=None,
                description="Built FastAPI services.",
            )
        ],
        projects=[
            SimpleNamespace(
                id=uuid4(),
                name="API Platform",
                start_date=None,
                end_date=None,
                description="Built PostgreSQL APIs.",
                technologies="FastAPI PostgreSQL",
            )
        ],
        education=[],
        certifications=[],
        achievements=[],
        links=[],
    )
    requirement = SimpleNamespace(
        text="Build APIs",
        importance=1.0,
        skills=[SimpleNamespace(skill=fastapi)],
    )
    job = SimpleNamespace(
        id=uuid4(),
        title="Backend Engineer",
        company="Example",
        requirements=[requirement],
    )

    document, gap = build_role_specific_resume(profile, job)

    assert document.metadata["target_role"] == "Backend Engineer"
    assert "FastAPI" in [skill.name for skill in document.skills]
    assert any(item.title == "Backend Intern" for item in document.experience)
    assert gap.keyword_coverage == 1.0
    assert validate_resume_document(document) == []


def test_builder_does_not_create_missing_skill_claim():
    python = SimpleNamespace(id=uuid4(), name="Python")
    profile = SimpleNamespace(
        id=uuid4(),
        user=SimpleNamespace(display_name="Candidate"),
        headline=None,
        summary=None,
        skills=[SimpleNamespace(skill=python)],
        experience=[],
        projects=[],
        education=[],
        certifications=[],
        achievements=[],
        links=[],
    )
    requirement = SimpleNamespace(
        text="Use Kubernetes",
        importance=1.0,
        skills=[SimpleNamespace(skill=SimpleNamespace(id=uuid4(), name="Kubernetes"))],
    )
    job = SimpleNamespace(
        id=uuid4(),
        title="DevOps Engineer",
        company="Example",
        requirements=[requirement],
    )

    document, gap = build_role_specific_resume(profile, job)

    assert [skill.name for skill in document.skills] == []
    assert len(gap.gaps) == 1
    assert gap.gaps[0].matched is False


def test_builder_preserves_relevant_achievements_and_profile_links():
    python = SimpleNamespace(id=uuid4(), name="Python")
    achievement = SimpleNamespace(
        id=uuid4(),
        title="Hackathon Winner",
        description="Built a Python automation platform.",
        organization="Example",
        achievement_date=None,
        url="https://example.com/achievement",
    )
    link = SimpleNamespace(
        id=uuid4(),
        platform="GitHub",
        label="GitHub",
        url="https://github.com/example",
    )
    profile = SimpleNamespace(
        id=uuid4(),
        user=SimpleNamespace(display_name="Candidate"),
        headline="Backend Developer",
        summary=None,
        skills=[SimpleNamespace(skill=python)],
        experience=[],
        projects=[],
        education=[],
        certifications=[],
        achievements=[achievement],
        links=[link],
    )
    job = SimpleNamespace(
        id=uuid4(),
        title="Python Engineer",
        company="Example",
        requirements=[
            SimpleNamespace(
                text="Build Python systems",
                importance=1.0,
                skills=[SimpleNamespace(skill=python)],
            )
        ],
    )

    document, _ = build_role_specific_resume(profile, job)

    assert len(document.achievements) == 1
    assert "Python automation" in document.achievements[0].text
    assert document.links[0].text == "GitHub: https://github.com/example"

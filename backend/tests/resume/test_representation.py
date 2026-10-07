from types import SimpleNamespace
from uuid import uuid4

from app.services.resume.representation import build_resume_representation


def test_build_resume_representation_keeps_profile_facts():
    project_id = uuid4()
    skill = SimpleNamespace(name="FastAPI")
    profile = SimpleNamespace(
        headline="Backend Developer",
        summary="Builds APIs",
        skills=[SimpleNamespace(skill=skill)],
        experience=[],
        projects=[
            SimpleNamespace(
                id=project_id,
                name="CareerPilot",
                description="Built a backend",
                technologies="FastAPI PostgreSQL",
            )
        ],
        certifications=[],
    )

    result = build_resume_representation(profile, target_keywords={"fastapi"})

    assert result.headline == "Backend Developer"
    assert result.summary == "Builds APIs"
    assert result.skills == ["FastAPI"]
    assert result.selected_content[0].source_id == str(project_id)
    assert result.selected_content[0].text == "Built a backend"

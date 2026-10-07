from types import SimpleNamespace

from app.services.resume.job_gap import analyze_job_requirements


def test_analyze_job_requirements_separates_gaps_and_matches():
    fastapi = SimpleNamespace(name="FastAPI")
    postgres = SimpleNamespace(name="PostgreSQL")

    requirements = [
        SimpleNamespace(
            text="Build APIs with FastAPI",
            importance=1.0,
            skills=[SimpleNamespace(skill=fastapi)],
        ),
        SimpleNamespace(
            text="Experience with Kubernetes",
            importance=0.5,
            skills=[],
        ),
        SimpleNamespace(
            text="Work with PostgreSQL",
            importance=1.0,
            skills=[SimpleNamespace(skill=postgres)],
        ),
    ]

    result = analyze_job_requirements(requirements, {"FastAPI", "PostgreSQL"})

    assert len(result.matched_requirements) == 2
    assert len(result.gaps) == 1
    assert result.gaps[0].requirement == "Experience with Kubernetes"
    assert result.keyword_coverage == 2 / 3


def test_empty_requirements_are_fully_covered():
    result = analyze_job_requirements([], {"Python"})

    assert result.keyword_coverage == 1.0

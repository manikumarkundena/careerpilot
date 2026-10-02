from app.services.job_intelligence.extractor import (
    extract_requirements,
    extract_skills_from_text,
)
from app.services.job_intelligence.preprocessor import clean_job_description

def test_extract_requirements():
    text = """
    Requirements:
    - Strong knowledge of Python
    - Experience with FastAPI

    Preferred Qualifications:
    - Experience with React.js

    Responsibilities:
    - Build backend services
    """

    result = extract_requirements(text)

    assert len(result) == 4

    assert result[0]["requirement_type"] == "required"
    assert result[0]["text"] == "Strong knowledge of Python"

    assert result[1]["requirement_type"] == "required"
    assert result[1]["text"] == "Experience with FastAPI"

    assert result[2]["requirement_type"] == "preferred"
    assert result[2]["text"] == "Experience with React.js"

    assert result[3]["requirement_type"] == "responsibility"


def test_extract_skills():
    skill_lookup = {
        "python": type("Skill", (), {"name": "Python"})(),
        "fastapi": type("Skill", (), {"name": "FastAPI"})(),
        "react.js": type("Skill", (), {"name": "React"})(),
        "js": type("Skill", (), {"name": "JavaScript"})(),
        "typescript": type("Skill", (), {"name": "TypeScript"})(),
    }

    result = extract_skills_from_text(
        "Experience with React.js and TypeScript",
        skill_lookup,
    )

    names = [skill["name"] for skill in result]

    assert names == ["React", "TypeScript"]


def test_extract_multiple_skills():
    skill_lookup = {
        "python": type("Skill", (), {"name": "Python"})(),
        "fastapi": type("Skill", (), {"name": "FastAPI"})(),
        "docker": type("Skill", (), {"name": "Docker"})(),
    }

    result = extract_skills_from_text(
        "Strong knowledge of Python and FastAPI with Docker",
        skill_lookup,
    )

    names = [skill["name"] for skill in result]

    assert names == [
        "Python",
        "FastAPI",
        "Docker",
    ]


def test_extract_skills_empty_text():
    skill_lookup = {
        "python": type("Skill", (), {"name": "Python"})(),
    }

    result = extract_skills_from_text(
        "",
        skill_lookup,
    )

    assert result == []

def test_clean_job_description_preserves_words():
    text = """
    Good understanding of Git

    Experience with React.js and TypeScript
    """

    result = clean_job_description(text)

    assert "understanding of Git" in result
    assert "React.js and TypeScript" in result
from types import SimpleNamespace

from app.services.resume.jd_intelligence import (
    candidate_keyword_coverage,
    candidate_skill_matches_requirement_text,
    extract_requirement_keywords,
)


def requirement(text, importance, *skills):
    return SimpleNamespace(
        text=text,
        importance=importance,
        skills=[
            SimpleNamespace(skill=SimpleNamespace(name=name))
            for name in skills
        ],
    )


def test_extracts_linked_skills_and_filters_generic_jd_words():
    result = extract_requirement_keywords(
        [
            requirement(
                "Build APIs with FastAPI and PostgreSQL",
                1.0,
                "FastAPI",
                "PostgreSQL",
            ),
            requirement(
                "Experience with Kubernetes",
                0.5,
            ),
        ]
    )

    names = {item.text.casefold() for item in result.keywords}
    assert {"fastapi", "postgresql", "kubernetes"} <= names
    assert "build" not in names
    assert "apis" not in names


def test_candidate_coverage_never_treats_jd_keywords_as_candidate_evidence():
    requirements = [
        requirement("Experience with Kubernetes", 1.0),
        requirement("Build APIs with FastAPI", 0.5, "FastAPI"),
    ]

    overall, must_have, preferred = candidate_keyword_coverage(
        requirements,
        {"FastAPI"},
    )

    assert overall > 0.0
    assert must_have == 0.0
    assert preferred > 0.0


def test_matches_multiword_candidate_skills_in_raw_jd_text():
    matches = candidate_skill_matches_requirement_text(
        "Build services using Spring Boot and REST API.",
        {"Spring Boot", "REST API", "React.js"},
    )

    assert matches == ("REST API", "Spring Boot")

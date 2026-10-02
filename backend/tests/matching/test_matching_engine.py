import pytest

from app.services.matching.requirement_matcher import match_requirement
from app.services.matching.service import (
    calculate_requirement_coverage,
    calculate_skill_coverage,
    match_candidate_to_job,
)
from app.services.matching.skill_matcher import match_skills


# ============================================================
# Skill Matching
# ============================================================


def test_match_skills_exact_case_insensitive_match():
    candidate_skills = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
        "PostgreSQL": "Intermediate",
    }

    required_skills = [
        "python",
        "FASTAPI",
        "Docker",
    ]

    matches, missing = match_skills(
        candidate_skills,
        required_skills,
    )

    assert len(matches) == 3

    assert matches[0].matched is True
    assert matches[0].skill_name == "python"
    assert matches[0].proficiency == "Advanced"

    assert matches[1].matched is True
    assert matches[1].skill_name == "FASTAPI"
    assert matches[1].proficiency == "Intermediate"

    assert matches[2].matched is False

    assert missing == ["Docker"]


def test_match_skills_when_all_skills_match():
    candidate_skills = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
    }

    required_skills = [
        "Python",
        "FastAPI",
    ]

    matches, missing = match_skills(
        candidate_skills,
        required_skills,
    )

    assert all(match.matched for match in matches)
    assert missing == []


def test_match_skills_when_no_skills_match():
    candidate_skills = {
        "Java": "Advanced",
        "Spring": "Intermediate",
    }

    required_skills = [
        "Python",
        "FastAPI",
    ]

    matches, missing = match_skills(
        candidate_skills,
        required_skills,
    )

    assert all(not match.matched for match in matches)
    assert missing == ["Python", "FastAPI"]


# ============================================================
# Requirement Matching
# ============================================================


def test_requirement_matches_when_required_skill_exists():
    candidate_skills = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
    }

    result = match_requirement(
        requirement_type="required",
        requirement_text="Experience with Python backend development",
        importance=1.0,
        required_skills=["Python"],
        candidate_skills=candidate_skills,
    )

    assert result.matched is True
    assert result.matched_skills == ["Python"]
    assert result.importance == 1.0


def test_requirement_does_not_match_when_skill_is_missing():
    candidate_skills = {
        "Python": "Advanced",
    }

    result = match_requirement(
        requirement_type="required",
        requirement_text="Experience with Docker",
        importance=1.0,
        required_skills=["Docker"],
        candidate_skills=candidate_skills,
    )

    assert result.matched is False
    assert result.matched_skills == []


def test_requirement_default_importance():
    candidate_skills = {
        "Python": "Advanced",
    }

    result = match_requirement(
        requirement_type="preferred",
        requirement_text="Python experience preferred",
        importance=None,
        required_skills=["Python"],
        candidate_skills=candidate_skills,
    )

    assert result.importance == 0.5
    assert result.matched is True


# ============================================================
# Skill Coverage
# ============================================================


def test_skill_coverage_partial_match():
    candidate_skills = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
    }

    required_skills = [
        "Python",
        "FastAPI",
        "Docker",
        "PostgreSQL",
    ]

    coverage = calculate_skill_coverage(
        candidate_skills,
        required_skills,
    )

    assert coverage == 0.5


def test_skill_coverage_full_match():
    candidate_skills = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
        "Docker": "Intermediate",
    }

    required_skills = [
        "Python",
        "FastAPI",
        "Docker",
    ]

    coverage = calculate_skill_coverage(
        candidate_skills,
        required_skills,
    )

    assert coverage == 1.0


def test_skill_coverage_no_required_skills():
    candidate_skills = {
        "Python": "Advanced",
    }

    coverage = calculate_skill_coverage(
        candidate_skills,
        [],
    )

    assert coverage == 1.0


# ============================================================
# Requirement Coverage
# ============================================================


def test_requirement_coverage_respects_importance():
    requirements = [
        match_requirement(
            requirement_type="required",
            requirement_text="Python",
            importance=1.0,
            required_skills=["Python"],
            candidate_skills={"Python": "Advanced"},
        ),
        match_requirement(
            requirement_type="required",
            requirement_text="Docker",
            importance=1.0,
            required_skills=["Docker"],
            candidate_skills={},
        ),
    ]

    coverage = calculate_requirement_coverage(
        requirements
    )

    assert coverage == 0.5


def test_requirement_coverage_weighted():
    requirements = [
        match_requirement(
            requirement_type="required",
            requirement_text="Python",
            importance=0.8,
            required_skills=["Python"],
            candidate_skills={"Python": "Advanced"},
        ),
        match_requirement(
            requirement_type="preferred",
            requirement_text="Docker",
            importance=0.2,
            required_skills=["Docker"],
            candidate_skills={},
        ),
    ]

    coverage = calculate_requirement_coverage(
        requirements
    )

    assert coverage == 0.8


def test_requirement_coverage_when_no_requirements():
    coverage = calculate_requirement_coverage([])

    assert coverage == 1.0


# ============================================================
# End-to-End Deterministic Matching
# ============================================================


def test_match_candidate_to_job():
    candidate_skills = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
        "PostgreSQL": "Intermediate",
    }

    required_skills = [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]

    requirements = [
        {
            "requirement_type": "required",
            "text": "Strong Python development experience",
            "importance": 1.0,
            "skills": ["Python"],
        },
        {
            "requirement_type": "required",
            "text": "FastAPI backend development",
            "importance": 1.0,
            "skills": ["FastAPI"],
        },
        {
            "requirement_type": "preferred",
            "text": "Docker experience",
            "importance": 0.5,
            "skills": ["Docker"],
        },
    ]

    result = match_candidate_to_job(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        requirements=requirements,
    )

    assert result.skill_coverage == 0.75

    assert result.requirement_coverage == pytest.approx(
        2.0 / 2.5
    )

    assert set(result.matched_skills) == {
        "Python",
        "FastAPI",
        "PostgreSQL",
    }

    assert result.missing_skills == ["Docker"]

    assert len(result.matched_requirements) == 3

    assert result.matched_requirements[0].matched is True
    assert result.matched_requirements[1].matched is True
    assert result.matched_requirements[2].matched is False

    assert result.gaps == [
        "Missing skill: Docker"
    ]

    assert result.score == pytest.approx(
        (
            0.75 * 0.6
            + (2.0 / 2.5) * 0.4
        )
        * 100,
        abs=0.01,
    )


# ============================================================
# Empty Candidate
# ============================================================


def test_empty_candidate_against_job():
    candidate_skills = {}

    required_skills = [
        "Python",
        "FastAPI",
        "Docker",
    ]

    requirements = [
        {
            "requirement_type": "required",
            "text": "Python experience",
            "importance": 1.0,
            "skills": ["Python"],
        },
        {
            "requirement_type": "required",
            "text": "Docker experience",
            "importance": 1.0,
            "skills": ["Docker"],
        },
    ]

    result = match_candidate_to_job(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        requirements=requirements,
    )

    assert result.skill_coverage == 0.0

    assert result.requirement_coverage == 0.0

    assert result.matched_skills == []

    assert result.missing_skills == [
        "Python",
        "FastAPI",
        "Docker",
    ]

    assert len(result.gaps) == 3

    assert result.score == 0.0

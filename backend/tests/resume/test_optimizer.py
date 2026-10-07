from app.services.resume.content_selector import ContentCandidate
from app.services.resume.job_gap import ResumeGapAnalysis
from app.services.resume.optimizer import optimize_resume_for_job


def test_optimizer_prioritizes_existing_facts_and_skills():
    candidates = [
        ContentCandidate(
            text="Built a React dashboard",
            source_type="project",
            source_id="react",
            keywords=("React",),
        ),
        ContentCandidate(
            text="Built a FastAPI service",
            source_type="project",
            source_id="fastapi",
            keywords=("FastAPI",),
        ),
    ]

    result = optimize_resume_for_job(
        candidates=candidates,
        candidate_skills=["FastAPI", "React"],
        target_keywords={"FastAPI"},
    )

    assert result.selected_content[0].source_id == "fastapi"
    assert result.prioritized_skills == ("FastAPI",)
    assert result.covered_keywords == ("FastAPI",)
    assert result.uncovered_keywords == ()


def test_optimizer_does_not_add_missing_skills():
    result = optimize_resume_for_job(
        candidates=[],
        candidate_skills=["Python"],
        target_keywords={"Python", "Kubernetes"},
    )

    assert result.prioritized_skills == ("Python",)
    assert "Kubernetes" in result.uncovered_keywords


def test_optimizer_accepts_gap_analysis_without_mutating_facts():
    gap_analysis = ResumeGapAnalysis(
        gaps=(),
        matched_requirements=(),
        keyword_coverage=1.0,
    )

    result = optimize_resume_for_job(
        candidates=[
            ContentCandidate(
                text="Original fact",
                source_type="experience",
                source_id="1",
            )
        ],
        candidate_skills=[],
        target_keywords=set(),
        gap_analysis=gap_analysis,
    )

    assert result.selected_content[0].text == "Original fact"

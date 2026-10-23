from types import SimpleNamespace

from app.services.resume.quality import evaluate_resume_quality
from app.services.resume.job_gap import ResumeGap, ResumeGapAnalysis
from app.services.resume.schema import ResumeDocument, ResumeSkill, ResumeSource, ResumeText


def source(source_id="1"):
    return ResumeSource("profile", source_id, "summary")


def test_quality_report_measures_job_alignment_without_fake_ats_score():
    document = ResumeDocument(
        name=ResumeText("Candidate", source()),
        summary=ResumeText("Backend developer", source()),
        skills=[ResumeSkill("FastAPI", ResumeSource("skill", "s1", "name"))],
        projects=[
            SimpleNamespace(
                title="Project",
            )
        ],
    )
    gap_analysis = ResumeGapAnalysis(
        gaps=(ResumeGap("Kubernetes", 1.0, False),),
        matched_requirements=(
            ResumeGap("FastAPI", 1.0, True, ("FastAPI",)),
        ),
        keyword_coverage=0.5,
    )

    report = evaluate_resume_quality(document, gap_analysis)

    assert report.keyword_coverage == 0.5
    assert report.required_skills_covered == 1
    assert report.required_skills_total == 2
    assert "skills" in report.sections_present
    assert report.passed


def test_quality_flags_low_keyword_coverage():
    document = ResumeDocument(
        name=ResumeText("Candidate", source()),
        skills=[ResumeSkill("Python", ResumeSource("skill", "s1", "name"))],
    )
    gap_analysis = ResumeGapAnalysis(
        gaps=(
            ResumeGap("FastAPI", 1.0, False),
            ResumeGap("Kubernetes", 1.0, False),
        ),
        matched_requirements=(),
        keyword_coverage=0.0,
    )

    report = evaluate_resume_quality(document, gap_analysis)

    assert any(issue.code == "low_keyword_coverage" for issue in report.issues)


def test_quality_flags_missing_candidate_name():
    document = ResumeDocument(
        skills=[ResumeSkill("Python", ResumeSource("skill", "s1", "name"))],
    )
    gap_analysis = ResumeGapAnalysis(
        gaps=(),
        matched_requirements=(),
        keyword_coverage=1.0,
    )

    report = evaluate_resume_quality(document, gap_analysis)

    assert any(issue.code == "missing_name" for issue in report.issues)
    assert report.passed is False



def test_readiness_score_is_explainable_and_recommendations_are_actionable():
    document = ResumeDocument(
        name=ResumeText("Candidate", source()),
        summary=ResumeText("Python backend developer", source()),
        skills=[
            ResumeSkill("Python", ResumeSource("skill", "s1", "name")),
            ResumeSkill("FastAPI", ResumeSource("skill", "s2", "name")),
        ],
        education=[SimpleNamespace(title="B.E. Computer Science")],
        projects=[SimpleNamespace(title="API project")],
    )
    gap_analysis = ResumeGapAnalysis(
        gaps=(ResumeGap("Kubernetes", 0.9, False),),
        matched_requirements=(ResumeGap("FastAPI", 1.0, True, ("FastAPI",)),),
        keyword_coverage=0.5,
    )

    report = evaluate_resume_quality(document, gap_analysis)

    assert 0 <= report.readiness_score <= 100
    assert report.score_components["job_keyword_alignment"] == 20
    assert report.score_components["required_skill_coverage"] == 15
    assert sum(report.score_components.values()) == report.readiness_score
    assert any("missing job requirements" in item for item in report.recommendations)

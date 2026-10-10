from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import resume as resume_route
from app.main import app
from app.models.job import Job
from app.services.resume.quality import ResumeQualityReport
from app.services.resume.schema import ResumeDocument


def make_client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_generate_resume_passes_ai_opt_in_and_marks_response(
    session,
    override_get_db,
    monkeypatch,
):
    email = f"resume-ai-opt-in-{uuid4()}@example.com"

    async with make_client() as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "display_name": "AI Resume Candidate",
            },
        )
        assert register.status_code == 201
        token = register.json()["access_token"]

    job = Job(
        source="test",
        external_id=f"job-{uuid4()}",
        title="Backend Engineer",
        company="Example",
        description="Build backend services.",
        is_active=True,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    fake_result = SimpleNamespace(
        pdf_bytes=b"%PDF-1.7\ncareerpilot AI opt-in test",
        document=ResumeDocument(),
        quality=ResumeQualityReport(
            keyword_coverage=0.75,
            required_skills_covered=3,
            required_skills_total=4,
            sections_present=(),
        ),
        ai_optimized=True,
    )

    def fake_generate(profile, loaded_job, *, optimize_with_ai=False):
        assert profile.user.email == email
        assert loaded_job.id == job.id
        assert optimize_with_ai is True
        return fake_result

    monkeypatch.setattr(
        resume_route,
        "generate_resume_pdf",
        fake_generate,
    )

    async with make_client() as client:
        response = await client.post(
            "/api/v1/resumes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "job_id": str(job.id),
                "optimize_with_ai": True,
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-resume-ai-optimized"] == "true"
    assert response.headers["x-resume-version"] == "1"
    assert response.content == fake_result.pdf_bytes

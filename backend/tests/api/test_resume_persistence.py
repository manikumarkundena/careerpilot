from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import resume as resume_route
from app.main import app
from app.models.job import Job
from app.services.resume.quality import ResumeQualityReport
from app.services.resume.schema import (
    ResumeDocument,
    ResumeSource,
    ResumeText,
)


def make_client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_generated_resume_version_persists_document_quality_and_pdf(
    session,
    override_get_db,
    monkeypatch,
):
    email = f"resume-persistence-{uuid4()}@example.com"
    async with make_client() as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "display_name": "Persistence Candidate",
            },
        )
    assert register.status_code == 201
    token = register.json()["access_token"]

    job = Job(
        source="test",
        external_id=f"resume-persistence-job-{uuid4()}",
        title="Backend Engineer",
        company="Example",
        description="Build backend services.",
        is_active=True,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    pdf_bytes = b"%PDF-1.7\nCareerPilot persisted PDF fixture"
    document = ResumeDocument(
        name=ResumeText(
            "Persistence Candidate",
            ResumeSource("profile", "candidate-1", "name"),
        ),
    )
    quality = ResumeQualityReport(
        keyword_coverage=0.75,
        required_skills_covered=3,
        required_skills_total=4,
        sections_present=("name",),
    )
    fake_result = SimpleNamespace(
        pdf_bytes=pdf_bytes,
        document=document,
        quality=quality,
        ai_optimized=False,
    )

    monkeypatch.setattr(
        resume_route,
        "generate_resume_pdf",
        lambda profile, loaded_job, *, optimize_with_ai=False: fake_result,
    )

    async with make_client() as client:
        generated = await client.post(
            "/api/v1/resumes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"job_id": str(job.id)},
        )
        assert generated.status_code == 200
        assert generated.content == pdf_bytes
        assert generated.headers["x-resume-version"] == "1"

        history = await client.get(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert history.status_code == 200
        versions = history.json()
        assert len(versions) == 1
        saved = versions[0]
        assert saved["version"] == 1
        assert saved["target_job_id"] == str(job.id)
        assert saved["pdf_sha256"] == sha256(pdf_bytes).hexdigest()

        detail = await client.get(
            f"/api/v1/resumes/{saved['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail.status_code == 200
        detail_json = detail.json()
        assert detail_json["document"]["name"]["text"] == "Persistence Candidate"
        assert detail_json["quality"]["keyword_coverage"] == 0.75
        assert detail_json["pdf_sha256"] == sha256(pdf_bytes).hexdigest()

        download = await client.get(
            f"/api/v1/resumes/{saved['id']}/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/pdf"
        assert download.headers["cache-control"] == "private, no-store"
        assert download.headers["x-resume-version"] == "1"
        assert download.content == pdf_bytes

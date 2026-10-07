from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.database import get_db
from app.main import app
from app.models.job import Job
from app.services.resume import generation as generation_module


def make_client():
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_generate_resume_requires_authentication(
    session,
    override_get_db,
):
    async with make_client() as client:
        response = await client.post(
            "/api/v1/resumes/generate",
            json={"job_id": str(uuid4())},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_generate_resume_returns_404_for_missing_job(
    session,
    override_get_db,
):
    email = f"resume-missing-{uuid4()}@example.com"

    async with make_client() as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )
        token = register.json()["access_token"]

        response = await client.post(
            "/api/v1/resumes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"job_id": str(uuid4())},
        )

    assert response.status_code == 422
    assert any(
        error["loc"][-1] == "profile_id"
        and error["type"] == "extra_forbidden"
        for error in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_generate_resume_uses_authenticated_profile_and_returns_pdf(
    session,
    override_get_db,
    monkeypatch,
):
    email = f"resume-success-{uuid4()}@example.com"

    async with make_client() as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "display_name": "Resume Candidate",
            },
        )
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
        pdf_bytes=b"%PDF-1.7\ncareerpilot test pdf",
        quality=SimpleNamespace(
            keyword_coverage=0.75,
            passed=True,
        ),
    )

    def fake_generate(profile, loaded_job):
        assert profile.user.email == email
        assert loaded_job.id == job.id
        return fake_result

    monkeypatch.setattr(
        generation_module,
        "generate_resume_pdf",
        fake_generate,
    )

    async with make_client() as client:
        response = await client.post(
            "/api/v1/resumes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"job_id": str(job.id)},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="careerpilot-resume.pdf"'
    )
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-resume-keyword-coverage"] == "0.75"
    assert response.headers["x-resume-quality-passed"] == "true"
    assert response.content == fake_result.pdf_bytes


@pytest.mark.asyncio
async def test_generate_resume_does_not_accept_profile_id(
    session,
    override_get_db,
):
    email = f"resume-schema-{uuid4()}@example.com"

    async with make_client() as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )
        token = register.json()["access_token"]

        response = await client.post(
            "/api/v1/resumes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "job_id": str(uuid4()),
                "profile_id": str(uuid4()),
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

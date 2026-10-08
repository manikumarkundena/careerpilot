from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_version import ResumeVersion
from app.services.resume.generation import ResumeGenerationResult


def _json_value(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def serialize_document(document: Any) -> dict[str, Any]:
    return _json_value(document)


def serialize_quality_report(report: Any) -> dict[str, Any]:
    return _json_value(report)


async def persist_resume_version(
    session: AsyncSession,
    profile_id: UUID,
    target_job_id: UUID,
    result: ResumeGenerationResult,
    template_version: str = "1",
) -> ResumeVersion:
    # Serialize the result before opening the transaction so database state is
    # only changed after the PDF has already passed all generation checks.
    document_json = serialize_document(result.document)
    quality_json = serialize_quality_report(result.quality)
    pdf_sha256 = sha256(result.pdf_bytes).hexdigest()

    async with session.begin_nested():
        # Serialize version allocation per profile to avoid duplicate versions
        # when two requests generate resumes concurrently for the same profile.
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:profile_id))"),
            {"profile_id": str(profile_id)},
        )
        current_max = await session.scalar(
            select(func.max(ResumeVersion.version)).where(
                ResumeVersion.profile_id == profile_id,
            )
        )
        version = (current_max or 0) + 1

        resume = ResumeVersion(
            profile_id=profile_id,
            target_job_id=target_job_id,
            version=version,
            template_version=template_version,
            document_json=document_json,
            quality_report_json=quality_json,
            pdf_bytes=result.pdf_bytes,
            pdf_sha256=pdf_sha256,
        )
        session.add(resume)
        await session.flush()
        await session.refresh(resume)

    return resume

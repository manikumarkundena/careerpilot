from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.services.job_ingestion.fingerprint import (
    generate_job_content_hash,
)
from app.services.job_ingestion.url_normalizer import (
    normalize_job_url,
)


class JobIngestionService:
    """
    Core job ingestion service.

    Responsible for:
    - normalizing job URLs
    - generating content fingerprints
    - detecting duplicate jobs
    - creating new Job records
    - updating existing jobs when appropriate
    """

    async def ingest(
        self,
        session: AsyncSession,
        *,
        source: str,
        title: str,
        company: str,
        description: str,
        external_id: str | None = None,
        location: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        application_url: str | None = None,
        posted_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[Job, bool]:
        canonical_url = None

        if application_url:
            canonical_url = normalize_job_url(application_url)

        content_hash = generate_job_content_hash(
            title=title,
            company=company,
            location=location,
            description=description,
        )

        existing_job = await self._find_duplicate(
            session,
            source=source,
            external_id=external_id,
            canonical_url=canonical_url,
            content_hash=content_hash,
        )

        if existing_job:
            self._update_existing_job(
                existing_job,
                title=title,
                company=company,
                description=description,
                location=location,
                employment_type=employment_type,
                experience_level=experience_level,
                application_url=application_url,
                canonical_url=canonical_url,
                content_hash=content_hash,
                posted_at=posted_at,
                expires_at=expires_at,
            )

            await session.commit()
            await session.refresh(existing_job)

            return existing_job, False

        job = Job(
            source=source,
            external_id=external_id,
            canonical_url=canonical_url,
            content_hash=content_hash,
            title=title,
            company=company,
            location=location,
            description=description,
            employment_type=employment_type,
            experience_level=experience_level,
            application_url=application_url,
            posted_at=posted_at,
            expires_at=expires_at,
            is_active=True,
        )

        session.add(job)

        await session.commit()
        await session.refresh(job)

        return job, True

    async def _find_duplicate(
        self,
        session: AsyncSession,
        *,
        source: str,
        external_id: str | None,
        canonical_url: str | None,
        content_hash: str,
    ) -> Job | None:

        conditions = []

        if external_id:
            conditions.append(
                (Job.source == source)
                & (Job.external_id == external_id)
            )

        if canonical_url:
            conditions.append(
                Job.canonical_url == canonical_url
            )

        conditions.append(
            Job.content_hash == content_hash
        )

        result = await session.execute(
            select(Job)
            .where(or_(*conditions))
            .limit(1)
        )

        return result.scalar_one_or_none()

    @staticmethod
    def _update_existing_job(
        job: Job,
        *,
        title: str,
        company: str,
        description: str,
        location: str | None,
        employment_type: str | None,
        experience_level: str | None,
        application_url: str | None,
        canonical_url: str | None,
        content_hash: str,
        posted_at: datetime | None,
        expires_at: datetime | None,
    ) -> None:

        job.title = title
        job.company = company
        job.description = description
        job.location = location
        job.employment_type = employment_type
        job.experience_level = experience_level
        job.application_url = application_url
        job.canonical_url = canonical_url
        job.content_hash = content_hash
        job.posted_at = posted_at
        job.expires_at = expires_at
        job.is_active = True

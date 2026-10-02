from sqlalchemy.ext.asyncio import AsyncSession

from app.services.job_ingestion.adapters.base import JobSourceAdapter
from app.services.job_ingestion.service import JobIngestionService


class JobIngestionPipeline:
    def __init__(
        self,
        ingestion_service: JobIngestionService | None = None,
    ) -> None:
        self.ingestion_service = (
            ingestion_service or JobIngestionService()
        )

    async def run(
        self,
        session: AsyncSession,
        adapter: JobSourceAdapter,
    ) -> dict:
        jobs = await adapter.fetch_jobs()

        created = 0
        updated = 0

        for raw_job in jobs:
            _, was_created = await self.ingestion_service.ingest(
                session,
                source=raw_job.source,
                external_id=raw_job.external_id,
                title=raw_job.title,
                company=raw_job.company,
                location=raw_job.location,
                description=raw_job.description,
                employment_type=raw_job.employment_type,
                experience_level=raw_job.experience_level,
                application_url=raw_job.application_url,
                posted_at=raw_job.posted_at,
                expires_at=raw_job.expires_at,
            )

            if was_created:
                created += 1
            else:
                updated += 1

        return {
            "source": adapter.source_name,
            "fetched": len(jobs),
            "created": created,
            "updated": updated,
        }
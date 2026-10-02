from sqlalchemy.ext.asyncio import AsyncSession

from app.services.job_ingestion.pipeline import JobIngestionPipeline
from app.services.job_ingestion.registry import JobAdapterRegistry


class JobDiscoveryService:
    def __init__(
        self,
        registry: JobAdapterRegistry,
        pipeline: JobIngestionPipeline | None = None,
    ) -> None:
        self.registry = registry
        self.pipeline = pipeline or JobIngestionPipeline()

    async def discover(
        self,
        session: AsyncSession,
        *,
        source: str,
        query: str,
        location: str | None,
        page: int,
        limit: int,
    ) -> dict:
        adapter = self.registry.create(
            source,
            country="in",
            what=query,
            where=location,
            page=page,
            results_per_page=limit,
        )

        return await self.pipeline.run(
            session,
            adapter,
        )

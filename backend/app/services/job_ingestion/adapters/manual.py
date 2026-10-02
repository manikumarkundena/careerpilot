from app.services.job_ingestion.adapters.base import (
    JobSourceAdapter,
    RawJob,
)


class ManualJobAdapter(JobSourceAdapter):
    """Adapter for jobs supplied manually by the user/application."""

    def __init__(self, jobs: list[RawJob]) -> None:
        self.jobs = jobs

    @property
    def source_name(self) -> str:
        return "manual"

    async def fetch_jobs(self) -> list[RawJob]:
        return self.jobs
from app.services.job_ingestion.adapters.adzuna import AdzunaAdapter
from app.services.job_ingestion.adapters.base import (
    JobSourceAdapter,
    RawJob,
)
from app.services.job_ingestion.adapters.manual import (
    ManualJobAdapter,
)

__all__ = [
    "AdzunaAdapter",
    "JobSourceAdapter",
    "RawJob",
    "ManualJobAdapter",
]

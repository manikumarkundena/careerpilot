from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RawJob:
    source: str
    title: str
    company: str
    description: str

    external_id: str | None = None
    location: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    application_url: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None


class JobSourceAdapter(ABC):
    """Contract every job source adapter must implement."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the canonical source identifier."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_jobs(self) -> list[RawJob]:
        """Fetch and return normalized raw jobs."""
        raise NotImplementedError
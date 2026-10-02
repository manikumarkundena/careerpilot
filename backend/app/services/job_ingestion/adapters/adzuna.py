from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings
from app.services.job_ingestion.adapters.base import (
    JobSourceAdapter,
    RawJob,
)


class AdzunaAdapter(JobSourceAdapter):
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        *,
        country: str = "in",
        what: str = "software engineer",
        where: str | None = None,
        page: int = 1,
        results_per_page: int = 20,
    ) -> None:
        self.country = country
        self.what = what
        self.where = where
        self.page = page
        self.results_per_page = results_per_page

    @property
    def source_name(self) -> str:
        return "adzuna"

    async def fetch_jobs(self) -> list[RawJob]:
        if not settings.adzuna_app_id:
            raise RuntimeError("ADZUNA_APP_ID is not configured")

        if not settings.adzuna_app_key:
            raise RuntimeError("ADZUNA_APP_KEY is not configured")

        url = f"{self.BASE_URL}/{self.country}/search/{self.page}"

        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "what": self.what,
            "results_per_page": self.results_per_page,
        }

        if self.where:
            params["where"] = self.where

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        return [
            self._to_raw_job(item)
            for item in data.get("results", [])
        ]

    def _to_raw_job(self, item: dict[str, Any]) -> RawJob:
        company = item.get("company") or {}
        location = item.get("location") or {}

        return RawJob(
            source=self.source_name,
            external_id=self._string_or_none(item.get("id")),
            title=item.get("title") or "Untitled Job",
            company=company.get("display_name") or "Unknown Company",
            description=item.get("description") or "",
            location=location.get("display_name"),
            employment_type=self._map_contract_type(
                item.get("contract_type")
            ),
            experience_level=None,
            application_url=item.get("redirect_url"),
            posted_at=self._parse_datetime(
                item.get("created")
            ),
        )

    @staticmethod
    def _string_or_none(value: Any) -> str | None:
        if value is None:
            return None

        return str(value)

    @staticmethod
    def _map_contract_type(
        value: str | None,
    ) -> str | None:
        if not value:
            return None

        return value

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None
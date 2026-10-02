from collections.abc import Callable

from app.services.job_ingestion.adapters.adzuna import AdzunaAdapter
from app.services.job_ingestion.adapters.base import JobSourceAdapter
from app.services.job_ingestion.adapters.manual import ManualJobAdapter


AdapterFactory = Callable[..., JobSourceAdapter]


class JobAdapterRegistry:
    def __init__(
        self,
        factories: dict[str, AdapterFactory] | None = None,
    ) -> None:
        self._factories: dict[str, AdapterFactory] = factories or {}

    def register(
        self,
        source: str,
        factory: AdapterFactory,
    ) -> None:
        self._factories[source] = factory

    def create(
        self,
        source: str,
        **kwargs,
    ) -> JobSourceAdapter:
        factory = self._factories.get(source)

        if factory is None:
            raise ValueError(
                f"No adapter registered for source: {source}"
            )

        return factory(**kwargs)

    def available_sources(self) -> list[str]:
        return sorted(self._factories.keys())


def create_default_registry() -> JobAdapterRegistry:
    registry = JobAdapterRegistry()

    registry.register(
        "adzuna",
        AdzunaAdapter,
    )

    registry.register(
        "manual",
        lambda jobs: ManualJobAdapter(jobs),
    )

    return registry
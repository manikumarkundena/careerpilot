from pydantic import BaseModel, Field


class JobDiscoveryRequest(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=100,
    )

    query: str = Field(
        min_length=1,
        max_length=255,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=50,
    )


class JobDiscoveryResponse(BaseModel):
    source: str
    query: str
    location: str | None
    fetched: int
    created: int
    updated: int

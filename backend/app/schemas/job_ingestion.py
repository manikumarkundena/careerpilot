from pydantic import BaseModel, Field


class JobIngestItem(BaseModel):
    external_id: str | None = Field(
        default=None,
        max_length=255,
    )
    title: str = Field(
        min_length=1,
        max_length=255,
    )
    company: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str = Field(
        min_length=1,
    )
    location: str | None = Field(
        default=None,
        max_length=255,
    )
    employment_type: str | None = Field(
        default=None,
        max_length=100,
    )
    experience_level: str | None = Field(
        default=None,
        max_length=100,
    )
    application_url: str | None = Field(
        default=None,
        max_length=1000,
    )


class JobIngestRequest(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=100,
    )
    jobs: list[JobIngestItem] = Field(
        min_length=1,
    )


class JobIngestResponse(BaseModel):
    source: str
    fetched: int
    created: int
    updated: int
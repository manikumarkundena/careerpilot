from datetime import datetime

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    external_id: str | None = Field(default=None, max_length=255)

    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)

    location: str | None = Field(default=None, max_length=255)

    description: str = Field(min_length=1)

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

    posted_at: datetime | None = None
    expires_at: datetime | None = None

    is_active: bool = True


class JobResponse(BaseModel):
    id: str

    source: str
    external_id: str | None

    title: str
    company: str
    location: str | None

    description: str

    employment_type: str | None
    experience_level: str | None

    application_url: str | None

    posted_at: datetime | None
    expires_at: datetime | None

    is_active: bool

class JobListItem(BaseModel):
    id: str
    source: str
    external_id: str | None
    title: str
    company: str
    location: str | None
    employment_type: str | None
    experience_level: str | None
    application_url: str | None
    posted_at: datetime | None
    is_active: bool


class JobListResponse(BaseModel):
    items: list[JobListItem]
    total: int
    page: int
    limit: int
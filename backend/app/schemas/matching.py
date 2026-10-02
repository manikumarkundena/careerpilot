from uuid import UUID

from pydantic import BaseModel, Field


class RequirementMatchResponse(BaseModel):
    requirement_text: str
    requirement_type: str
    importance: float
    matched: bool
    matched_skills: list[str] = Field(
        default_factory=list
    )


class MatchResponse(BaseModel):
    job_id: UUID
    score: float
    skill_coverage: float
    requirement_coverage: float

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    matched_requirements: list[
        RequirementMatchResponse
    ] = Field(
        default_factory=list
    )

    gaps: list[str] = Field(
        default_factory=list
    )
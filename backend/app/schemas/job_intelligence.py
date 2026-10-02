from pydantic import BaseModel, Field


class JobAnalyzeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class SkillResponse(BaseModel):
    name: str


class RequirementResponse(BaseModel):
    requirement_type: str
    text: str
    importance: float
    skills: list[SkillResponse]


class JobAnalyzeResponse(BaseModel):
    cleaned_text: str
    requirements: list[RequirementResponse]

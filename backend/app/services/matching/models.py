from dataclasses import dataclass, field


@dataclass(slots=True)
class SkillMatch:
    skill_name: str
    matched: bool
    proficiency: str | None = None


@dataclass(slots=True)
class RequirementMatch:
    requirement_text: str
    requirement_type: str
    importance: float
    matched: bool
    matched_skills: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MatchResult:
    skill_coverage: float
    requirement_coverage: float
    matched_skills: list[str]
    missing_skills: list[str]
    matched_requirements: list[RequirementMatch]
    gaps: list[str]

    @property
    def score(self) -> float:
        return round(
            (
                self.skill_coverage * 0.6
                + self.requirement_coverage * 0.4
            )
            * 100,
            2,
        )
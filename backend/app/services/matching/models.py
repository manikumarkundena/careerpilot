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
    semantic_similarity: float | None = None

    @property
    def score(self) -> float:
        from app.services.matching.hybrid import calculate_hybrid_score

        return calculate_hybrid_score(
            skill_coverage=self.skill_coverage,
            requirement_coverage=self.requirement_coverage,
            semantic_similarity=self.semantic_similarity,
        )

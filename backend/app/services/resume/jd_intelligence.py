from __future__ import annotations

import re
from dataclasses import dataclass


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "have",
    "in", "is", "it", "of", "on", "or", "our", "the", "to", "with", "you",
    "your", "will", "we", "this", "that", "their", "they", "work", "working",
    "experience", "years", "strong", "good", "ability", "knowledge", "skills", "api", "apis",
    "skill", "including", "using", "use", "develop", "development", "build",
    "building", "role", "team", "teams", "required", "preferred", "responsible",
}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#./-]{1,}")


@dataclass(slots=True, frozen=True)
class JobKeyword:
    text: str
    source: str
    importance: float


@dataclass(slots=True, frozen=True)
class JobRequirementIntelligence:
    keywords: tuple[JobKeyword, ...]
    must_have: tuple[JobKeyword, ...]
    preferred: tuple[JobKeyword, ...]


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _contains_term(text: str, term: str) -> bool:
    normalized_text = _normalize(text)
    normalized_term = _normalize(term)
    if not normalized_term:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_term) + r"(?![a-z0-9])"
    return bool(re.search(pattern, normalized_text))


def extract_requirement_keywords(requirements) -> JobRequirementIntelligence:
    """Extract deterministic, explainable keywords from structured requirements.

    Linked SkillCatalog entries are authoritative domain terms. Significant
    technical-looking terms from raw requirement text add coverage when a
    requirement was ingested without a linked skill. No extracted keyword is
    treated as candidate evidence.
    """
    by_key: dict[str, JobKeyword] = {}

    for requirement in requirements:
        importance = float(requirement.importance or 0.0)
        linked = [
            skill.skill.name
            for skill in requirement.skills
            if getattr(skill, "skill", None) is not None
        ]

        for name in linked:
            key = _normalize(name)
            if key:
                existing = by_key.get(key)
                if existing is None or importance > existing.importance:
                    by_key[key] = JobKeyword(name.strip(), "skill_catalog", importance)

        for token in _TOKEN_RE.findall(requirement.text or ""):
            if token.casefold() in _STOPWORDS:
                continue
            if len(token) < 3 and not any(ch.isdigit() for ch in token):
                continue
            key = _normalize(token)
            existing = by_key.get(key)
            candidate = JobKeyword(token, "requirement_text", importance)
            if existing is None or importance > existing.importance:
                by_key[key] = candidate

    keywords = tuple(
        sorted(
            by_key.values(),
            key=lambda item: (-item.importance, item.text.casefold()),
        )
    )

    must_have = tuple(item for item in keywords if item.importance >= 0.75)
    preferred = tuple(item for item in keywords if item.importance < 0.75)

    return JobRequirementIntelligence(
        keywords=keywords,
        must_have=must_have,
        preferred=preferred,
    )


def candidate_keyword_coverage(
    requirements,
    candidate_skill_names: set[str],
) -> tuple[float, float, float]:
    """Return overall, must-have, and preferred keyword coverage.

    Only candidate skills can satisfy a keyword. Job text never creates a
    candidate skill or evidence claim.
    """
    intelligence = extract_requirement_keywords(requirements)
    normalized_candidates = {
        _normalize(name) for name in candidate_skill_names if name.strip()
    }

    def covered(items: tuple[JobKeyword, ...]) -> float:
        if not items:
            return 1.0
        matched = 0
        for item in items:
            if _normalize(item.text) in normalized_candidates:
                matched += 1
        return matched / len(items)

    return (
        covered(intelligence.keywords),
        covered(intelligence.must_have),
        covered(intelligence.preferred),
    )


def candidate_skill_matches_requirement_text(
    requirement_text: str,
    candidate_skill_names: set[str],
) -> tuple[str, ...]:
    """Find profile skills explicitly present in a raw requirement."""
    matches = [
        skill
        for skill in candidate_skill_names
        if skill.strip() and _contains_term(requirement_text or "", skill)
    ]
    return tuple(sorted(matches, key=str.casefold))

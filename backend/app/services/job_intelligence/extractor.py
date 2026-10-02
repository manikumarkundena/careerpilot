import re


SECTION_PATTERNS = {
    "required": [
        r"requirements?",
        r"required qualifications?",
        r"basic qualifications?",
        r"minimum qualifications?",
        r"must have",
        r"required skills?",
    ],
    "preferred": [
        r"preferred qualifications?",
        r"preferred skills?",
        r"nice to have",
        r"good to have",
        r"desired qualifications?",
    ],
    "responsibility": [
        r"responsibilities",
        r"what you.ll do",
        r"what you will do",
        r"role and responsibilities",
        r"key responsibilities",
    ],
}


def _match_section(line: str) -> str | None:
    """
    Identify the requirement category represented by a heading.
    """
    normalized = line.strip().lower()

    # Remove trailing punctuation.
    normalized = re.sub(r"[:\-]+$", "", normalized).strip()

    for requirement_type, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalized):
                return requirement_type

    return None


def extract_requirements(text: str) -> list[dict[str, str]]:
    """
    Extract structured requirements from a cleaned job description.

    This is the deterministic baseline. Later, an AI/ML extractor
    can be added and evaluated against this baseline.
    """
    if not text:
        return []

    requirements: list[dict[str, str]] = []
    current_type: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # Detect section headings.
        section_type = _match_section(line)

        if section_type:
            current_type = section_type
            continue

        # Only treat bullet points as requirements.
        if current_type and re.match(r"^[-*]\s+", line):
            requirement_text = re.sub(
                r"^[-*]\s+",
                "",
                line,
            ).strip()

            if requirement_text:
                requirements.append(
                    {
                        "requirement_type": current_type,
                        "text": requirement_text,
                    }
                )

    return requirements

import re


SECTION_PATTERNS = {
    "required": [
        r"requirements?",
        r"required qualifications?",
        r"basic qualifications?",
        r"minimum qualifications?",
        r"must have",
        r"required skills?",
    ],
    "preferred": [
        r"preferred qualifications?",
        r"preferred skills?",
        r"nice to have",
        r"good to have",
        r"desired qualifications?",
    ],
    "responsibility": [
        r"responsibilities",
        r"what you.ll do",
        r"what you will do",
        r"role and responsibilities",
        r"key responsibilities",
    ],
}


def _match_section(line: str) -> str | None:
    """
    Identify the requirement category represented by a heading.
    """
    normalized = line.strip().lower()

    # Remove trailing punctuation.
    normalized = re.sub(r"[:\-]+$", "", normalized).strip()

    for requirement_type, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalized):
                return requirement_type

    return None


def extract_requirements(text: str) -> list[dict[str, str]]:
    """
    Extract structured requirements from a cleaned job description.

    This is the deterministic baseline. Later, an AI/ML extractor
    can be added and evaluated against this baseline.
    """
    if not text:
        return []

    requirements: list[dict[str, str]] = []
    current_type: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # Detect section headings.
        section_type = _match_section(line)

        if section_type:
            current_type = section_type
            continue

        # Only treat bullet points as requirements.
        if current_type and re.match(r"^[-*]\s+", line):
            requirement_text = re.sub(
                r"^[-*]\s+",
                "",
                line,
            ).strip()

            if requirement_text:
                requirements.append(
                    {
                        "requirement_type": current_type,
                        "text": requirement_text,
                    }
                )

    return requirements

def extract_skills_from_text(
    text: str,
    skill_lookup: dict[str, object],
) -> list[dict[str, str]]:
    """
    Extract known skills from requirement text using the
    canonical skill lookup.

    The lookup keys should already be normalized.
    """

    if not text:
        return []

    normalized_text = text.lower()

    matches: list[tuple[int, int, str]] = []

    for alias, skill in skill_lookup.items():
        if not alias:
            continue

        pattern = rf"(?<![\w.]){re.escape(alias)}(?!\w)"
        for match in re.finditer(pattern, normalized_text):
            canonical_name = skill.name

            matches.append(
                (
                    match.start(),
                    match.end(),
                    canonical_name,
                )
            )

    # Prefer longer matches when aliases overlap.
    matches.sort(
        key=lambda item: (
            item[0],
            -(item[1] - item[0]),
        )
    )

    extracted: list[dict[str, str]] = []
    seen: set[str] = set()

    for _, _, canonical_name in matches:
        if canonical_name in seen:
            continue

        seen.add(canonical_name)

        extracted.append(
            {
                "name": canonical_name,
            }
        )

    return extracted
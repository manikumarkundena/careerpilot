import re


IMPORTANCE_PATTERNS = {
    "high": [
        r"\brequired\b",
        r"\bmust\b",
        r"\bmandatory\b",
        r"\bminimum\b",
        r"\bstrong knowledge\b",
        r"\bproficien(?:t|cy)\b",
        r"\bexpert(?:ise)?\b",
    ],
    "medium": [
        r"\bexperience with\b",
        r"\bexperience in\b",
        r"\bknowledge of\b",
        r"\bfamiliar(?:ity)? with\b",
        r"\bunderstanding of\b",
    ],
    "low": [
        r"\bpreferred\b",
        r"\bnice to have\b",
        r"\bgood to have\b",
        r"\bbonus\b",
        r"\bplus\b",
    ],
}


IMPORTANCE_VALUES = {
    "high": 0.9,
    "medium": 0.6,
    "low": 0.3,
}


def classify_importance(
    text: str,
    requirement_type: str,
) -> float:
    """
    Estimate requirement importance using transparent rules.

    Returns a value between 0.0 and 1.0.
    """

    if not text:
        return 0.0

    normalized = text.lower()

    # Section-level classification provides a strong baseline.
    if requirement_type == "required":
        base_importance = 0.8
    elif requirement_type == "preferred":
        base_importance = 0.4
    elif requirement_type == "responsibility":
        base_importance = 0.5
    else:
        base_importance = 0.5

    # Explicit wording can strengthen or weaken the score.
    for pattern in IMPORTANCE_PATTERNS["high"]:
        if re.search(pattern, normalized):
            return IMPORTANCE_VALUES["high"]

    for pattern in IMPORTANCE_PATTERNS["low"]:
        if re.search(pattern, normalized):
            return IMPORTANCE_VALUES["low"]

    for pattern in IMPORTANCE_PATTERNS["medium"]:
        if re.search(pattern, normalized):
            return IMPORTANCE_VALUES["medium"]

    return base_importance

import hashlib
import re


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)

    return value


def generate_job_content_hash(
    *,
    title: str,
    company: str,
    location: str | None,
    description: str,
) -> str:
    """
    Generate a deterministic SHA-256 fingerprint for a job.

    The fingerprint is based on normalized job identity/content fields.
    """

    normalized_values = [
        _normalize_text(company),
        _normalize_text(title),
        _normalize_text(location),
        _normalize_text(description),
    ]

    canonical_content = "\n".join(normalized_values)

    return hashlib.sha256(
        canonical_content.encode("utf-8")
    ).hexdigest()

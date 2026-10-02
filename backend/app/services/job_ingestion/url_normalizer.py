from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


def normalize_job_url(url: str) -> str:
    """
    Normalize a job URL while preserving meaningful URL components.

    Removes common tracking parameters and normalizes:
    - scheme
    - hostname casing
    - default ports
    - trailing slash
    - tracking query parameters
    """
    if not url:
        return ""

    url = url.strip()

    parsed = urlsplit(url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid job URL")

    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    if not hostname:
        raise ValueError("Invalid job URL")

    # Preserve non-default ports.
    netloc = hostname

    if parsed.port is not None:
        is_default_port = (
            (scheme == "http" and parsed.port == 80)
            or (scheme == "https" and parsed.port == 443)
        )

        if not is_default_port:
            netloc = f"{hostname}:{parsed.port}"

    # Remove tracking parameters while preserving meaningful ones.
    query_pairs = parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )

    filtered_query = [
        (key, value)
        for key, value in query_pairs
        if key.lower() not in TRACKING_PARAMETERS
    ]

    query = urlencode(filtered_query, doseq=True)

    # Normalize trailing slash except for root.
    path = parsed.path or "/"

    if path != "/":
        path = path.rstrip("/")

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            query,
            "",
        )
    )

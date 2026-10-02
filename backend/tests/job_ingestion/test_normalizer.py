import pytest

from app.services.job_ingestion.url_normalizer import (
    normalize_job_url,
)


def test_normalize_removes_tracking_parameters():
    url = (
        "https://example.com/jobs/123/"
        "?utm_source=linkedin&utm_campaign=test"
    )

    assert normalize_job_url(url) == (
        "https://example.com/jobs/123"
    )


def test_normalize_preserves_meaningful_query_parameters():
    url = (
        "https://example.com/jobs/123"
        "?page=2&utm_source=linkedin"
    )

    assert normalize_job_url(url) == (
        "https://example.com/jobs/123?page=2"
    )


def test_normalize_lowercases_hostname():
    url = "HTTPS://Example.COM/jobs/123/"

    assert normalize_job_url(url) == (
        "https://example.com/jobs/123"
    )


def test_normalize_rejects_invalid_url():
    with pytest.raises(ValueError):
        normalize_job_url("not-a-url")

from app.services.job_ingestion.fingerprint import (
    generate_job_content_hash,
)


def test_same_job_generates_same_hash():
    hash_one = generate_job_content_hash(
        title="Software Engineer Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build backend services with Python.",
    )

    hash_two = generate_job_content_hash(
        title=" software engineer intern ",
        company="EXAMPLE CORP",
        location="bangalore",
        description="Build   backend services with Python.",
    )

    assert hash_one == hash_two


def test_different_jobs_generate_different_hashes():
    hash_one = generate_job_content_hash(
        title="Software Engineer Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build backend services.",
    )

    hash_two = generate_job_content_hash(
        title="Data Science Intern",
        company="Example Corp",
        location="Bangalore",
        description="Build machine learning models.",
    )

    assert hash_one != hash_two


def test_hash_is_sha256():
    result = generate_job_content_hash(
        title="Software Engineer",
        company="Example",
        location="Remote",
        description="Build software.",
    )

    assert len(result) == 64
    assert all(
        character in "0123456789abcdef"
        for character in result
    )

from app.services.resume.artifact import build_pdf_artifact_report


def test_pdf_artifact_report_accepts_valid_extractable_pdf():
    pdf = b"%PDF-1.7" + b"x" * 200

    report = build_pdf_artifact_report(
        pdf,
        "Candidate\nBackend Developer\nFastAPI",
        ["Candidate", "FastAPI"],
    )

    assert report.passed is True
    assert report.missing_expected_text == ()


def test_pdf_artifact_report_detects_missing_content():
    pdf = b"%PDF-1.7" + b"x" * 200

    report = build_pdf_artifact_report(
        pdf,
        "Candidate\nBackend Developer",
        ["Candidate", "FastAPI"],
    )

    assert report.passed is False
    assert report.missing_expected_text == ("FastAPI",)


def test_pdf_artifact_report_includes_page_count_and_accepts_one_page():
    from app.services.resume.artifact import build_pdf_artifact_report

    report = build_pdf_artifact_report(
        b"%PDF-1.7" + b"x" * 200,
        "Candidate\\nFastAPI",
        ["Candidate", "FastAPI"],
        page_count=1,
    )

    assert report.page_count == 1
    assert report.passed is True


def test_pdf_artifact_report_rejects_resume_spilling_to_multiple_pages():
    from app.services.resume.artifact import build_pdf_artifact_report

    report = build_pdf_artifact_report(
        b"%PDF-1.7" + b"x" * 200,
        "Candidate\\nFastAPI",
        ["Candidate", "FastAPI"],
        page_count=2,
    )

    assert report.page_count == 2
    assert report.passed is False

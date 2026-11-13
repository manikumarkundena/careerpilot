import json
from urllib.error import URLError

import pytest

from app.services.resume.generation import (
    ResumeOptimizationProviderError,
    ResumeOptimizationTimeoutError,
    _request_llm,
)


def test_request_llm_maps_timeout_to_timeout_error(monkeypatch):
    def fake_urlopen(request, timeout):
        raise TimeoutError("sensitive transport detail")

    monkeypatch.setattr("app.services.resume.generation.urlopen", fake_urlopen)

    with pytest.raises(ResumeOptimizationTimeoutError) as error:
        _request_llm("https://llm.example.test", {}, {}, 1.0)

    assert str(error.value) == "AI provider request timed out"


def test_request_llm_maps_network_error_without_leaking_details(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("private network detail")

    monkeypatch.setattr("app.services.resume.generation.urlopen", fake_urlopen)

    with pytest.raises(ResumeOptimizationProviderError) as error:
        _request_llm("https://llm.example.test", {}, {}, 1.0)

    assert str(error.value).startswith("AI provider request failed")
    assert "private network detail" not in str(error.value)


def test_request_llm_maps_malformed_provider_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"not-json"

    monkeypatch.setattr(
        "app.services.resume.generation.urlopen",
        lambda request, timeout: FakeResponse(),
    )

    with pytest.raises(ResumeOptimizationProviderError, match="unusable response"):
        _request_llm("https://llm.example.test", {}, {}, 1.0)


def test_request_llm_extracts_chat_completion(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "[ ]"}}]}
            ).encode("utf-8")

    monkeypatch.setattr(
        "app.services.resume.generation.urlopen",
        lambda request, timeout: FakeResponse(),
    )

    assert _request_llm("https://llm.example.test", {}, {}, 1.0) == "[ ]"



def _generation_artifact(*, page_count, missing=()):
    from types import SimpleNamespace

    passed = page_count == 1 and not missing
    return SimpleNamespace(
        valid_pdf_signature=True,
        byte_size=500,
        extractable_text="Candidate Backend developer",
        missing_expected_text=tuple(missing),
        page_count=page_count,
        passed=passed,
    )


def _prepare_generation_mocks(monkeypatch, artifact_reports, rendered_modes, compiled_pdfs):
    from types import SimpleNamespace

    from app.services.resume.schema import ResumeDocument, ResumeSource, ResumeText

    document = ResumeDocument(
        name=ResumeText(
            "Candidate",
            ResumeSource("profile", "user-1", "name"),
        ),
        headline=ResumeText(
            "Backend developer",
            ResumeSource("profile", "user-1", "headline"),
        ),
    )
    monkeypatch.setattr(
        "app.services.resume.generation.build_role_specific_resume",
        lambda profile, job: (document, None),
    )
    monkeypatch.setattr(
        "app.services.resume.generation.validate_resume_document",
        lambda candidate: [],
    )
    monkeypatch.setattr(
        "app.services.resume.generation.evaluate_resume_quality",
        lambda candidate, gaps: SimpleNamespace(passed=True),
    )

    def fake_render(candidate, *, compact=False):
        rendered_modes.append(compact)
        return "compact" if compact else "standard"

    monkeypatch.setattr(
        "app.services.resume.generation.render_resume_latex",
        fake_render,
    )
    monkeypatch.setattr(
        "app.services.resume.generation.compile_latex_to_pdf",
        lambda source: compiled_pdfs.pop(0),
    )
    monkeypatch.setattr(
        "app.services.resume.generation.validate_pdf_artifact",
        lambda pdf, expected: artifact_reports.pop(0),
    )


def test_generation_retries_compact_layout_for_multipage_pdf(monkeypatch):
    from app.services.resume.generation import generate_resume_pdf

    rendered_modes = []
    compiled_pdfs = [b"first-pdf", b"compact-pdf"]
    _prepare_generation_mocks(
        monkeypatch,
        [
            _generation_artifact(page_count=2),
            _generation_artifact(page_count=1),
        ],
        rendered_modes,
        compiled_pdfs,
    )

    result = generate_resume_pdf(object(), object())

    assert rendered_modes == [False, True]
    assert result.pdf_bytes == b"compact-pdf"
    assert result.artifact.page_count == 1


def test_generation_does_not_retry_when_expected_text_is_missing(monkeypatch):
    from app.services.resume.generation import (
        ResumeGenerationArtifactError,
        generate_resume_pdf,
    )

    rendered_modes = []
    compiled_pdfs = [b"first-pdf"]
    _prepare_generation_mocks(
        monkeypatch,
        [_generation_artifact(page_count=1, missing=("Candidate",))],
        rendered_modes,
        compiled_pdfs,
    )

    with pytest.raises(ResumeGenerationArtifactError):
        generate_resume_pdf(object(), object())

    assert rendered_modes == [False]

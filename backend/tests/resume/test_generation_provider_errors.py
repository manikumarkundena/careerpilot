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

    assert str(error.value) == "AI provider request failed"
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

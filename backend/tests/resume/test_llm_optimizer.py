import json

import pytest

from app.services.resume.ai_optimizer import ResumeOptimizationValidationError
from app.services.resume.llm_optimizer import LLMOptimizerConfig, LLMResumeOptimizer
from app.services.resume.schema import ResumeDocument, ResumeEntry, ResumeSource, ResumeText


def _document() -> ResumeDocument:
    source = ResumeSource("project", "project-1", "description")
    return ResumeDocument(
        projects=[
            ResumeEntry(
                title="CareerPilot",
                organization=None,
                location=None,
                dates=None,
                bullets=[ResumeText("Built a FastAPI platform", source)],
                source=source,
            )
        ]
    )


def _optimizer(response: str) -> LLMResumeOptimizer:
    def fake_request(endpoint, payload, headers, timeout):
        assert endpoint == "https://llm.example.test/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert payload["model"] == "test-model"
        assert timeout == 5.0
        return response

    return LLMResumeOptimizer(
        LLMOptimizerConfig(
            endpoint="https://llm.example.test/v1/chat/completions",
            api_key="test-key",
            model="test-model",
            timeout_seconds=5.0,
        ),
        request=fake_request,
    )


def test_llm_optimizer_accepts_source_grounded_response():
    response = json.dumps(
        [{
            "source_type": "project",
            "source_id": "project-1",
            "field": "description",
            "original_text": "Built a FastAPI platform",
            "proposed_text": "Built a FastAPI platform for backend workflows",
            "rationale": "Improves wording without adding a new fact.",
        }]
    )

    proposals = _optimizer(response).propose(_document(), {"FastAPI"})

    assert proposals[0].proposed_text.endswith("backend workflows")


def test_llm_optimizer_rejects_invalid_json():
    with pytest.raises(ResumeOptimizationValidationError, match="valid JSON"):
        _optimizer("not-json").propose(_document(), {"FastAPI"})


def test_llm_optimizer_rejects_unknown_source():
    response = json.dumps(
        [{
            "source_type": "project",
            "source_id": "not-real",
            "field": "description",
            "original_text": "Built a FastAPI platform",
            "proposed_text": "Built a Kubernetes platform",
        }]
    )

    with pytest.raises(ResumeOptimizationValidationError, match="unknown source"):
        _optimizer(response).propose(_document(), {"Kubernetes"})

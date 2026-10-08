from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from app.services.resume.ai_optimizer import (
    ResumeOptimizationProposal,
    ResumeOptimizationValidationError,
    validate_optimization_proposals,
)
from app.services.resume.schema import ResumeDocument, ResumeSource, ResumeText


@dataclass(slots=True, frozen=True)
class LLMOptimizerConfig:
    endpoint: str
    api_key: str
    model: str
    timeout_seconds: float = 30.0


class LLMResumeOptimizer:
    """Untrusted LLM provider whose output must pass provenance validation."""

    def __init__(
        self,
        config: LLMOptimizerConfig,
        *,
        request: Callable[[str, dict, dict, float], str],
    ) -> None:
        self.config = config
        self._request = request

    def propose(self, document: ResumeDocument, target_keywords: set[str]) -> list[ResumeOptimizationProposal]:
        raw = self._request(
            self.config.endpoint,
            {
                "model": self.config.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Rewrite only verified source text. Never invent facts, "
                            "metrics, skills, employers, dates, technologies, or achievements. "
                            "Return a JSON array only."
                        ),
                    },
                    {"role": "user", "content": _build_prompt(document, target_keywords)},
                ],
            },
            {"Authorization": f"Bearer {self.config.api_key}"},
            self.config.timeout_seconds,
        )
        proposals = _parse_proposals(raw)
        validate_optimization_proposals(document, proposals)
        return proposals


def _build_prompt(document: ResumeDocument, target_keywords: set[str]) -> str:
    sources = [
        {
            "source_type": item.source.source_type,
            "source_id": item.source.source_id,
            "field": item.source.field,
            "text": item.text,
        }
        for item in _iter_resume_text(document)
    ]
    return json.dumps(
        {
            "target_keywords": sorted(target_keywords),
            "verified_sources": sources,
            "required_fields": [
                "source_type",
                "source_id",
                "field",
                "original_text",
                "proposed_text",
                "rationale",
            ],
        },
        ensure_ascii=False,
    )


def _parse_proposals(raw: str) -> list[ResumeOptimizationProposal]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResumeOptimizationValidationError("LLM response is not valid JSON") from exc

    if not isinstance(payload, list):
        raise ResumeOptimizationValidationError("LLM response must be a JSON array")

    proposals: list[ResumeOptimizationProposal] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ResumeOptimizationValidationError(f"proposal[{index}] must be an object")
        try:
            proposals.append(
                ResumeOptimizationProposal(
                    source=ResumeSource(
                        source_type=item["source_type"],
                        source_id=str(item["source_id"]),
                        field=str(item["field"]),
                    ),
                    original_text=str(item["original_text"]),
                    proposed_text=str(item["proposed_text"]),
                    rationale=str(item["rationale"]) if item.get("rationale") is not None else None,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ResumeOptimizationValidationError(
                f"proposal[{index}] has an invalid schema"
            ) from exc
    return proposals


def _iter_resume_text(document: ResumeDocument):
    if document.name:
        yield document.name
    if document.headline:
        yield document.headline
    if document.summary:
        yield document.summary
    for skill in document.skills:
        yield ResumeText(text=skill.name, source=skill.source)
    for entry in (
        *document.experience,
        *document.projects,
        *document.education,
        *document.certifications,
    ):
        yield from entry.bullets
    yield from document.achievements
    yield from document.links

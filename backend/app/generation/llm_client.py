from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import Settings
from app.schemas.api import CitationResponse


logger = logging.getLogger(__name__)

FALLBACK_NOT_FOUND = "I could not find the answer in the provided documents."


@dataclass(slots=True)
class GenerationResult:
    answer: str
    status: str
    llm_used: bool


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = (
            OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=settings.openai_timeout_seconds,
            )
            if settings.openai_api_key
            else None
        )

    def generate(
        self,
        question: str,
        messages: list[dict[str, str]],
        citations: list[CitationResponse],
    ) -> GenerationResult:
        if not citations:
            return GenerationResult(answer=FALLBACK_NOT_FOUND, status="not_found", llm_used=False)

        if self.client is None:
            logger.warning("OPENAI_API_KEY is not configured. Returning extractive fallback answer.")
            lead = citations[0]
            answer = (
                f"OpenAI generation is not configured, but the strongest evidence is from "
                f"{lead.filename} page {lead.page_number}"
            )
            if lead.section_title:
                answer += f" in {lead.section_title}"
            answer += f": {lead.snippet}"
            return GenerationResult(answer=answer, status="retrieval_only", llm_used=False)

        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=self.settings.openai_temperature,
            messages=messages,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            return GenerationResult(answer=FALLBACK_NOT_FOUND, status="not_found", llm_used=True)
        if FALLBACK_NOT_FOUND in content:
            return GenerationResult(answer=FALLBACK_NOT_FOUND, status="not_found", llm_used=True)
        return GenerationResult(answer=content, status="grounded_answer", llm_used=True)

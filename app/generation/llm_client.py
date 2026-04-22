from __future__ import annotations

import logging

from openai import OpenAI

from app.core.config import Settings
from app.generation.prompting import build_messages
from app.models.domain import RetrievalResult


logger = logging.getLogger(__name__)


class OpenAICompatibleGenerator:
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

    def generate_answer(self, question: str, results: list[RetrievalResult]) -> str:
        if not results:
            return "I could not find the answer in the provided documents"

        if self.client is None:
            logger.warning("OPENAI_API_KEY is not configured. Returning retrieval-only fallback.")
            return (
                "I could not generate a final answer because OPENAI_API_KEY is not configured. "
                "Relevant source chunks are returned below."
            )

        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=self.settings.openai_temperature,
            messages=build_messages(question, results),
        )
        content = response.choices[0].message.content or ""
        return content.strip() or "I could not find the answer in the provided documents"

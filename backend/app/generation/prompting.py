from __future__ import annotations

from app.schemas.domain import RetrievedPassage


SYSTEM_PROMPT = """You are a strict grounded assistant for document question answering.
Answer only from the supplied context.
Do not use outside knowledge.
If the context is insufficient, answer exactly: "I could not find the answer in the provided documents."
Keep the response concise, supported, and include inline citations in the format [filename p.X | section title].
If multiple citations support one point, include the strongest relevant citation only."""


def build_context(passages: list[RetrievedPassage]) -> str:
    blocks: list[str] = []
    for index, passage in enumerate(passages, start=1):
        unit = passage.unit
        section_title = unit.section_title or "Untitled section"
        blocks.append(
            "\n".join(
                [
                    f"[Evidence {index}]",
                    f"Document: {unit.filename}",
                    f"Pages: {unit.start_page}-{unit.end_page}",
                    f"Section: {section_title}",
                    f"Score: {passage.score:.4f}",
                    "Content:",
                    unit.text,
                ]
            )
        )
    return "\n\n".join(blocks)


def build_messages(question: str, context: str) -> list[dict[str, str]]:
    user_prompt = f"""Question:
{question}

Context:
{context}

Return a grounded answer only if the context supports it.
If the answer is absent or ambiguous in the context, use the fallback sentence exactly."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

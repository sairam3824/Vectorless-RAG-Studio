from __future__ import annotations

from app.models.domain import RetrievalResult


SYSTEM_PROMPT = """You are a careful RAG assistant.
Answer only from the supplied context.
Do not use outside knowledge.
If the answer is not supported by the context, say exactly: "I could not find the answer in the provided documents".
When you answer, include citations using the format [filename | chunk_id].
Keep the answer concise but complete."""


def build_context(results: list[RetrievalResult]) -> str:
    sections: list[str] = []
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        sections.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"filename: {chunk.filename}",
                    f"chunk_id: {chunk.id}",
                    f"score: {result.score:.4f}",
                    "content:",
                    chunk.text,
                ]
            )
        )
    return "\n\n".join(sections)


def build_messages(question: str, results: list[RetrievalResult]) -> list[dict[str, str]]:
    context = build_context(results)
    user_prompt = f"""Question:
{question}

Context:
{context}

Return a direct answer grounded in the context above.
If the evidence is incomplete, use the fallback sentence exactly.
Always include citations for factual claims."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

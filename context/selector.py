from __future__ import annotations

from pydantic import BaseModel


class ContextChunk(BaseModel):
    content: str
    source: str
    score: float


class ContextSelector:
    def select(self, chunks: list[ContextChunk], limit: int = 8) -> list[ContextChunk]:
        ranked = sorted(chunks, key=lambda item: item.score, reverse=True)
        deduped: list[ContextChunk] = []
        seen: set[str] = set()
        for chunk in ranked:
            if chunk.content in seen:
                continue
            deduped.append(chunk)
            seen.add(chunk.content)
            if len(deduped) >= limit:
                break
        return deduped


context_selector = ContextSelector()

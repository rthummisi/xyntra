from __future__ import annotations

from pydantic import BaseModel


class NormalizedAttachment(BaseModel):
    kind: str
    media_type: str
    content: str
    metadata: dict = {}


def normalize_attachments(attachments: list[dict]) -> list[NormalizedAttachment]:
    normalized: list[NormalizedAttachment] = []
    for attachment in attachments:
        normalized.append(
            NormalizedAttachment(
                kind=attachment.get("kind", "file"),
                media_type=attachment.get("media_type", "application/octet-stream"),
                content=attachment.get("content", ""),
                metadata=attachment.get("metadata", {}),
            )
        )
    return normalized

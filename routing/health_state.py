from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderHealthState(BaseModel):
    provider: str
    healthy: bool = True
    failures: int = 0
    metadata: dict = Field(default_factory=dict)

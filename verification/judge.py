from __future__ import annotations

from pydantic import BaseModel


class JudgeResult(BaseModel):
    accepted: bool
    score: float
    rationale: str


class JudgeHook:
    def evaluate(self, content: str) -> JudgeResult:
        score = 1.0 if content.strip() else 0.0
        return JudgeResult(
            accepted=bool(content.strip()),
            score=score,
            rationale="Accepted" if content.strip() else "Empty output rejected",
        )


judge_hook = JudgeHook()

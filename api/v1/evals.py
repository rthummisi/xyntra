from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.eval_service import EvalRequest, EvalResult, eval_service

router = APIRouter(prefix="/evals", tags=["evals"])


class EvalResponse(BaseModel):
    results: list[EvalResult]


@router.post("", response_model=EvalResponse)
async def run_eval(payload: EvalRequest) -> EvalResponse:
    try:
        results = await eval_service.evaluate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvalResponse(results=results)

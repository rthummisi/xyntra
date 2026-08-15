from __future__ import annotations

from fastapi import APIRouter, Query

from memory.token_ledger import token_ledger

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("")
def get_token_table(limit: int = Query(default=100, le=500)):
    """
    Token usage ledger — one row per completed task.
    Columns: date, task, provider, model, prompt_tokens, completion_tokens,
             total_tokens, efficiency, efficiency_reason.
    """
    entries = token_ledger.all(limit=limit)
    rows = [
        {
            "date": e.timestamp[:10],
            "time": e.timestamp[11:19],
            "task": e.task_summary,
            "provider": e.provider,
            "model": e.model,
            "task_type": e.task_type,
            "prompt_tokens": e.prompt_tokens,
            "completion_tokens": e.completion_tokens,
            "total_tokens": e.total_tokens,
            "cache_hit": e.cache_hit,
            "efficiency": e.efficiency,
            "efficiency_reason": e.efficiency_reason,
        }
        for e in entries
    ]
    return {
        "totals": token_ledger.totals(),
        "rows": rows,
    }


@router.delete("")
def clear_token_ledger():
    """Wipe the in-memory and persisted ledger."""
    token_ledger._entries.clear()
    token_ledger._persist()
    return {"cleared": True}

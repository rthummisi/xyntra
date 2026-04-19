from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from context.assembler import context_assembler
from context.compactor import context_compactor
from context.selector import ContextChunk


def test_context_assembler_selects_ranked_unique_chunks() -> None:
    assembled = context_assembler.assemble(
        chunks=[
            ContextChunk(content="same", source="a", score=0.3),
            ContextChunk(content="better", source="b", score=0.9),
            ContextChunk(content="same", source="c", score=0.8),
        ],
        total_window=8000,
    )

    assert assembled.chunks[0].content == "better"
    assert len(assembled.chunks) == 2
    assert assembled.budget.total_window == 8000


async def test_context_compactor_creates_summary_when_threshold_exceeded() -> None:
    session_id = uuid.uuid4()
    original_session_store = context_compactor.compact_if_needed.__globals__[
        "session_memory_store"
    ]
    original_summary_store = context_compactor.compact_if_needed.__globals__[
        "summary_memory_store"
    ]
    mocked_summary_store = SimpleNamespace(create_summary=AsyncMock())
    context_compactor.compact_if_needed.__globals__["session_memory_store"] = (
        SimpleNamespace(
            fetch_messages=AsyncMock(
                return_value=[
                    SimpleNamespace(role="user", content="one two three four five"),
                    SimpleNamespace(
                        role="assistant", content="six seven eight nine ten"
                    ),
                ]
            )
        )
    )
    context_compactor.compact_if_needed.__globals__["summary_memory_store"] = (
        mocked_summary_store
    )

    try:
        compacted = await context_compactor.compact_if_needed(
            None,
            session_id=session_id,
            token_threshold=3,
        )
    finally:
        context_compactor.compact_if_needed.__globals__["session_memory_store"] = (
            original_session_store
        )
        context_compactor.compact_if_needed.__globals__["summary_memory_store"] = (
            original_summary_store
        )

    assert compacted is True
    mocked_summary_store.create_summary.assert_awaited_once()


async def test_context_compactor_skips_when_threshold_not_exceeded() -> None:
    session_id = uuid.uuid4()
    original_session_store = context_compactor.compact_if_needed.__globals__[
        "session_memory_store"
    ]
    context_compactor.compact_if_needed.__globals__["session_memory_store"] = (
        SimpleNamespace(
            fetch_messages=AsyncMock(
                return_value=[SimpleNamespace(role="user", content="short text")]
            )
        )
    )

    try:
        compacted = await context_compactor.compact_if_needed(
            None,
            session_id=session_id,
            token_threshold=10,
        )
    finally:
        context_compactor.compact_if_needed.__globals__["session_memory_store"] = (
            original_session_store
        )

    assert compacted is False

from __future__ import annotations

from pydantic import BaseModel, Field

from context.selector import ContextChunk, context_selector
from context.token_budget import TokenBudget, token_budget_allocator


class AssembledContext(BaseModel):
    chunks: list[ContextChunk] = Field(default_factory=list)
    budget: TokenBudget


class ContextAssembler:
    def assemble(
        self,
        *,
        chunks: list[ContextChunk],
        total_window: int,
    ) -> AssembledContext:
        selected = context_selector.select(chunks)
        budget = token_budget_allocator.allocate(total_window=total_window)
        return AssembledContext(chunks=selected, budget=budget)


context_assembler = ContextAssembler()

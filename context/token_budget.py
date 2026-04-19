from __future__ import annotations

from pydantic import BaseModel


class TokenBudget(BaseModel):
    total: int
    reserved_for_output: int
    available_for_context: int

    @property
    def total_window(self) -> int:
        return self.total


class TokenBudgetAllocator:
    def allocate(
        self,
        *,
        total_window: int,
        reserved_for_output: int = 2048,
    ) -> TokenBudget:
        available = max(total_window - reserved_for_output, 0)
        return TokenBudget(
            total=total_window,
            reserved_for_output=reserved_for_output,
            available_for_context=available,
        )


token_budget_allocator = TokenBudgetAllocator()

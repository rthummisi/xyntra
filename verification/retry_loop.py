from __future__ import annotations

from collections.abc import Awaitable, Callable

from verification.validators import ValidationResult


class VerificationRetryLoop:
    async def run(
        self,
        operation: Callable[[], Awaitable[dict]],
        validator: Callable[[dict], ValidationResult],
        *,
        max_attempts: int = 3,
    ) -> tuple[dict, ValidationResult, int]:
        last_payload: dict = {}
        last_result = ValidationResult(valid=False, errors=["No attempts made."])
        for attempt in range(1, max_attempts + 1):
            last_payload = await operation()
            last_result = validator(last_payload)
            if last_result.valid:
                return last_payload, last_result, attempt
        return last_payload, last_result, max_attempts


verification_retry_loop = VerificationRetryLoop()

from __future__ import annotations

from routing.health_state import ProviderHealthState


class CircuitBreaker:
    def __init__(self) -> None:
        self._states: dict[str, ProviderHealthState] = {}

    def is_available(self, provider_name: str) -> bool:
        state = self._states.get(provider_name)
        return True if state is None else state.healthy

    def record_failure(self, provider_name: str) -> None:
        state = self._states.setdefault(
            provider_name,
            ProviderHealthState(provider=provider_name),
        )
        state.failures += 1
        if state.failures >= 3:
            state.healthy = False

    def record_success(self, provider_name: str) -> None:
        self._states[provider_name] = ProviderHealthState(provider=provider_name)

    def get_states(self) -> list[ProviderHealthState]:
        return list(self._states.values())


circuit_breaker = CircuitBreaker()

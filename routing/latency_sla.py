from __future__ import annotations


class LatencySLAEnforcer:
    def within_sla(
        self,
        *,
        expected_latency_ms: int,
        max_latency_ms: int | None,
    ) -> bool:
        if max_latency_ms is None:
            return True
        return expected_latency_ms <= max_latency_ms


latency_sla_enforcer = LatencySLAEnforcer()

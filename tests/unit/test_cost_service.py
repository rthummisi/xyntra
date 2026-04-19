from __future__ import annotations

from services.cost_service import cost_service


def test_quota_evaluation_flags_threshold_and_excess() -> None:
    threshold = cost_service.evaluate_quota(consumed_tokens=80, token_quota=100)
    exceeded = cost_service.evaluate_quota(consumed_tokens=120, token_quota=100)

    assert threshold["allowed"] is True
    assert threshold["threshold_reached"] is True
    assert exceeded["allowed"] is False
    assert exceeded["exceeded"] is True


def test_quota_evaluation_handles_missing_quota() -> None:
    payload = cost_service.evaluate_quota(consumed_tokens=500, token_quota=None)

    assert payload["allowed"] is True
    assert payload["token_quota"] is None
    assert payload["threshold_reached"] is False

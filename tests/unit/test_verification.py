from verification.code_checks import code_patch_validator
from verification.judge import judge_hook
from verification.retry_loop import verification_retry_loop
from verification.validators import structured_output_validator


def test_structured_output_validator_detects_missing_fields() -> None:
    result = structured_output_validator.validate_required_fields(
        {"a": 1},
        ["a", "b"],
    )
    assert result.valid is False
    assert result.errors == ["b"]


def test_code_patch_validator_requires_patch_markers() -> None:
    result = code_patch_validator.validate_patch("print('hi')")
    assert result.valid is False


async def test_retry_loop_retries_until_valid() -> None:
    attempts = {"count": 0}

    async def operation() -> dict:
        attempts["count"] += 1
        if attempts["count"] < 2:
            return {"status": "missing"}
        return {"status": "ok", "result": "done"}

    payload, validation, attempt_count = await verification_retry_loop.run(
        operation,
        lambda item: structured_output_validator.validate_required_fields(
            item,
            ["status", "result"],
        ),
    )

    assert validation.valid is True
    assert payload["result"] == "done"
    assert attempt_count == 2


def test_judge_hook_rejects_empty_content() -> None:
    result = judge_hook.evaluate("")
    assert result.accepted is False

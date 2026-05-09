from __future__ import annotations

from pathlib import Path

import pytest

import xyntra_cli
from services.contract_validation_service import contract_validation_service


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, *, headers: dict, json: dict) -> _FakeResponse:
        if "openai" in url:
            return _FakeResponse(
                {"choices": [{"message": {"content": "# ChatGPT Contract\n"}}]}
            )
        if "moonshot" in url:
            return _FakeResponse(
                {"choices": [{"message": {"content": "# Kimi Contract\n"}}]}
            )
        return _FakeResponse(
            {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "<<REFINED_CONTRACT>>\n# Final Contract\n"
                            "<<END_REFINED_CONTRACT>>\n"
                            "<<WHATS_INCLUDED>>\n"
                            "- Added clearer acceptance criteria\n"
                            "<<END_WHATS_INCLUDED>>"
                        ),
                    }
                ]
            }
        )


@pytest.mark.asyncio
async def test_contract_validation_creates_major_version_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "SPEC.md"
    source.write_text("# Original Contract\n", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("KIMI_API_KEY", "kimi-key")
    monkeypatch.setenv("KIMI_MODEL", "kimi-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setattr(
        "services.contract_validation_service.httpx.AsyncClient",
        _FakeAsyncClient,
    )

    result = await contract_validation_service.validate_contract(
        source_path=str(source),
        major_version=2,
        output_dir=str(tmp_path / "out"),
        kimi_model="kimi-test",
    )

    assert result.version == "2.0.0"
    assert Path(result.output_path).read_text(encoding="utf-8") == "# Final Contract\n"
    assert "Added clearer acceptance criteria" in Path(
        result.release_notes_path
    ).read_text(encoding="utf-8")
    assert Path(result.audit_path).exists()


@pytest.mark.asyncio
async def test_slash_command_parses_validation_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_validate_contract_file(**kwargs):
        class _Result:
            version = "3.0.0"
            output_path = "/tmp/spec-v3.0.0.md"
            release_notes_path = "/tmp/spec-v3.0.0-WHATS_INCLUDED.md"
            audit_path = "/tmp/spec-v3.0.0-validation.json"

        assert kwargs["source_path"] == "./SPEC.md"
        assert kwargs["major_version"] == 3
        assert kwargs["kimi_model"] == "kimi-k2"
        return _Result()

    monkeypatch.setattr(
        xyntra_cli, "validate_contract_file", _fake_validate_contract_file
    )

    result = await xyntra_cli.handle_contract_validation_command(
        "/coding projects validation ./SPEC.md --major-version 3 --kimi-model kimi-k2"
    )

    assert "Major contract version 3.0.0 created." in result
    assert "/tmp/spec-v3.0.0.md" in result

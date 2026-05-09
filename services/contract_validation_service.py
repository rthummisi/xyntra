from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic import BaseModel

FINAL_CONTRACT_START = "<<REFINED_CONTRACT>>"
FINAL_CONTRACT_END = "<<END_REFINED_CONTRACT>>"
WHATS_INCLUDED_START = "<<WHATS_INCLUDED>>"
WHATS_INCLUDED_END = "<<END_WHATS_INCLUDED>>"


class ContractValidationStage(BaseModel):
    stage: str
    provider: str
    model: str
    content: str


class ContractValidationResult(BaseModel):
    source_path: str
    output_path: str
    release_notes_path: str
    audit_path: str
    version: str
    stages: list[ContractValidationStage]


@dataclass(slots=True)
class OpenAICompatibleConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


class ContractValidationService:
    async def validate_contract(
        self,
        *,
        source_path: str,
        major_version: int,
        output_dir: str | None = None,
        chatgpt_model: str = "gpt-4o",
        kimi_model: str | None = None,
        claude_model: str = "claude-sonnet-4-6",
    ) -> ContractValidationResult:
        source = Path(source_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            raise ValueError(f"Contract source not found: {source}")

        original = source.read_text(encoding="utf-8")
        if not original.strip():
            raise ValueError("Contract source is empty.")

        chatgpt = await self._run_openai_compatible_stage(
            stage="chatgpt",
            document=original,
            prompt=self._chatgpt_prompt(original),
            config=OpenAICompatibleConfig(
                provider="openai",
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=chatgpt_model,
            ),
        )

        kimi_stage = await self._run_openai_compatible_stage(
            stage="kimi",
            document=chatgpt.content,
            prompt=self._kimi_prompt(
                original_contract=original,
                chatgpt_contract=chatgpt.content,
            ),
            config=OpenAICompatibleConfig(
                provider="kimi",
                base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai"),
                api_key=os.getenv("KIMI_API_KEY", ""),
                model=kimi_model or os.getenv("KIMI_MODEL", ""),
            ),
        )

        claude_stage = await self._run_claude_stage(
            original_contract=original,
            chatgpt_contract=chatgpt.content,
            kimi_contract=kimi_stage.content,
            model=claude_model,
        )

        refined_contract, whats_included = self._parse_final_output(
            claude_stage.content
        )
        version = f"{major_version}.0.0"
        target_dir = (
            Path(output_dir).expanduser().resolve()
            if output_dir
            else source.parent / "contract_versions"
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        stem = self._slugify(source.stem)
        contract_path = target_dir / f"{stem}-v{version}.md"
        release_notes_path = target_dir / f"{stem}-v{version}-WHATS_INCLUDED.md"
        audit_path = target_dir / f"{stem}-v{version}-validation.json"

        contract_path.write_text(refined_contract.strip() + "\n", encoding="utf-8")
        release_notes_path.write_text(whats_included.strip() + "\n", encoding="utf-8")
        audit_path.write_text(
            json.dumps(
                {
                    "source_path": str(source),
                    "version": version,
                    "generated_at": datetime.now(UTC).isoformat(),
                    "stages": [
                        chatgpt.model_dump(),
                        kimi_stage.model_dump(),
                        claude_stage.model_dump(),
                    ],
                    "outputs": {
                        "contract_path": str(contract_path),
                        "release_notes_path": str(release_notes_path),
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return ContractValidationResult(
            source_path=str(source),
            output_path=str(contract_path),
            release_notes_path=str(release_notes_path),
            audit_path=str(audit_path),
            version=version,
            stages=[chatgpt, kimi_stage, claude_stage],
        )

    async def _run_openai_compatible_stage(
        self,
        *,
        stage: str,
        document: str,
        prompt: str,
        config: OpenAICompatibleConfig,
    ) -> ContractValidationStage:
        if not config.api_key:
            raise ValueError(
                f"{stage} validation requires {config.provider.upper()}_API_KEY."
            )
        if not config.model:
            raise ValueError(
                f"{stage} validation requires a model via --{stage}-model or env."
            )

        payload = {
            "model": config.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
        }
        if not document:
            raise ValueError("Validation document is empty.")

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{config.base_url.rstrip('/')}/v1/chat/completions",
                headers={
                    "authorization": f"Bearer {config.api_key}",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = ((data.get("choices") or [{}])[0].get("message") or {}).get(
            "content", ""
        )
        if not content.strip():
            raise ValueError(f"{stage} validation returned an empty response.")
        return ContractValidationStage(
            stage=stage,
            provider=config.provider,
            model=config.model,
            content=content,
        )

    async def _run_claude_stage(
        self,
        *,
        original_contract: str,
        chatgpt_contract: str,
        kimi_contract: str,
        model: str,
    ) -> ContractValidationStage:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("claude validation requires ANTHROPIC_API_KEY.")

        prompt = self._claude_prompt(
            original_contract=original_contract,
            chatgpt_contract=chatgpt_contract,
            kimi_contract=kimi_contract,
        )
        payload = {
            "model": model,
            "max_tokens": 8192,
            "system": self._system_prompt(),
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com').rstrip('/')}/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        blocks = data.get("content", [])
        content = "".join(
            block.get("text", "") for block in blocks if block.get("type") == "text"
        )
        if not content.strip():
            raise ValueError("claude validation returned an empty response.")
        return ContractValidationStage(
            stage="claude",
            provider="anthropic",
            model=model,
            content=content,
        )

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You refine software project specifications and coding contracts. "
            "Preserve scope, strengthen execution details, resolve ambiguity, "
            "and produce release-ready markdown for engineering teams."
        )

    @staticmethod
    def _chatgpt_prompt(document: str) -> str:
        return (
            "Refine the following software specification or coding contract. "
            "Preserve intent and scope, but make it more executable: tighten "
            "constraints, acceptance criteria, sequencing, test expectations, "
            "deliverables, interface contracts, and non-goals. Return only the "
            "refined markdown contract.\n\n"
            f"{document}"
        )

    @staticmethod
    def _kimi_prompt(
        *,
        original_contract: str,
        chatgpt_contract: str,
    ) -> str:
        return (
            "You are the second reviewer in a contract hardening pipeline. "
            "Use the original contract plus the ChatGPT refinement to produce a "
            "sharper execution contract. Remove duplication, expose edge cases, "
            "clarify hidden assumptions, and improve rollout sequencing. Return "
            "only the refined markdown contract.\n\n"
            "ORIGINAL CONTRACT\n"
            f"{original_contract}\n\n"
            "CHATGPT REFINEMENT\n"
            f"{chatgpt_contract}"
        )

    @classmethod
    def _claude_prompt(
        cls,
        *,
        original_contract: str,
        chatgpt_contract: str,
        kimi_contract: str,
    ) -> str:
        return (
            "You are the final reviewer in a multi-model contract validation "
            "pipeline. Build the final major-version project contract from the "
            "original source and the two prior refinements. Keep scope aligned "
            "to the source, but make the document cleaner, stricter, and more "
            "operationally executable.\n\n"
            "Return the result with these exact markers and no extra prose:\n"
            f"{FINAL_CONTRACT_START}\n"
            "<final markdown contract>\n"
            f"{FINAL_CONTRACT_END}\n"
            f"{WHATS_INCLUDED_START}\n"
            "- bullet list of what this major version includes\n"
            f"{WHATS_INCLUDED_END}\n\n"
            "ORIGINAL CONTRACT\n"
            f"{original_contract}\n\n"
            "CHATGPT REFINEMENT\n"
            f"{chatgpt_contract}\n\n"
            "KIMI REFINEMENT\n"
            f"{kimi_contract}"
        )

    @classmethod
    def _parse_final_output(cls, content: str) -> tuple[str, str]:
        contract_match = re.search(
            rf"{re.escape(FINAL_CONTRACT_START)}\s*(.*?)\s*{re.escape(FINAL_CONTRACT_END)}",
            content,
            re.DOTALL,
        )
        included_match = re.search(
            rf"{re.escape(WHATS_INCLUDED_START)}\s*(.*?)\s*{re.escape(WHATS_INCLUDED_END)}",
            content,
            re.DOTALL,
        )
        if contract_match is None or included_match is None:
            raise ValueError("Claude output did not include the expected markers.")
        return contract_match.group(1), included_match.group(1)

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return normalized or "contract"


contract_validation_service = ContractValidationService()

#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

TRANSCRIPT_CONTENT_LIMIT = 12000


def command_workdir(context: dict[str, object]) -> Path:
    repo_root = context.get("repo_root")
    cwd = context.get("cwd")
    base_dir = repo_root or cwd or os.getcwd()
    return Path(str(base_dir)).resolve()


def default_test_command(context: dict[str, object]) -> list[str]:
    base_dir = command_workdir(context)
    if (base_dir / "pyproject.toml").exists() and (base_dir / "tests").exists():
        return ["pytest"]
    if (base_dir / "package.json").exists():
        return ["npm", "test"]
    raise SystemExit(
        "No default test command detected. Use `xyntra test <command>` instead."
    )


def parse_command_text(raw: str) -> list[str]:
    try:
        parts = shlex.split(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid command: {exc}") from exc
    if not parts:
        raise SystemExit("Command cannot be empty.")
    return parts


def run_command(command: list[str], *, cwd: Path) -> dict[str, object]:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    assert process.stdout is not None
    try:
        for line in process.stdout:
            print(line, end="", flush=True)
            lines.append(line)
    finally:
        process.stdout.close()
    exit_code = process.wait()
    output = "".join(lines)
    if not output.endswith("\n"):
        print(flush=True)
    return {
        "command": command,
        "cwd": str(cwd),
        "exit_code": exit_code,
        "output": output,
    }


def build_command_messages(
    result: dict[str, object],
) -> tuple[str, str, list[dict[str, object]]]:
    command = " ".join(shlex.quote(str(part)) for part in result["command"])
    cwd = str(result["cwd"])
    exit_code = int(result["exit_code"])
    output = str(result["output"])
    truncated_output = output[:TRANSCRIPT_CONTENT_LIMIT]
    if len(output) > TRANSCRIPT_CONTENT_LIMIT:
        omitted = len(output) - TRANSCRIPT_CONTENT_LIMIT
        truncated_output += f"\n\n[output truncated: {omitted} additional chars]"

    command_message = f"$ {command}\n[cwd] {cwd}"
    output_message = f"[exit_code] {exit_code}\n{truncated_output or '[no output]'}"
    attachments = [
        {
            "type": "cli_command",
            "command": command,
            "cwd": cwd,
            "exit_code": exit_code,
            "output": output,
        }
    ]
    return command_message, output_message, attachments

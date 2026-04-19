#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from xyntra_cli_exec import (
    build_command_messages,
    command_workdir,
    default_test_command,
    parse_command_text,
    run_command,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
START_SCRIPT = ROOT_DIR / "scripts" / "start_xyntra.sh"
STATE_DIR = Path.home() / ".xyntra"
STATE_FILE = STATE_DIR / "cli_state.json"
DEFAULT_MODEL = "llama3.2:3b"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        env = os.environ.copy()
        if args.seed:
            env["SEED_DEV_DATA"] = "true"
        subprocess.run([str(START_SCRIPT)], cwd=ROOT_DIR, env=env, check=True)
        return

    ensure_stack_running()

    if args.command == "status":
        print_status()
        return

    if args.command == "reset-context":
        reset_context(current_context_key())
        print("Xyntra CLI context reset for this directory.")
        return

    if args.command == "run":
        context = ensure_context(local_only=not args.hosted)
        content = chat_once(
            prompt=args.prompt,
            model=args.model,
            context=context,
            stream=args.stream,
        )
        if not args.stream:
            print(content)
        return

    if args.command == "exec":
        context = ensure_context(local_only=not args.hosted)
        raise SystemExit(run_and_persist_command(context, args.exec_command))

    if args.command == "test":
        context = ensure_context(local_only=not args.hosted)
        test_command = args.test_command or default_test_command(context)
        raise SystemExit(run_and_persist_command(context, test_command))

    interactive_chat(model=args.model, local_only=not args.hosted)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xyntra")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--hosted", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    start = subparsers.add_parser("start")
    start.add_argument("--seed", action="store_true")

    subparsers.add_parser("status")
    reset = subparsers.add_parser("reset-context")
    reset.set_defaults(command="reset-context")

    run = subparsers.add_parser("run")
    run.add_argument("prompt")
    run.add_argument("--model", default=DEFAULT_MODEL)
    run.add_argument("--hosted", action="store_true")
    run.add_argument("--stream", action="store_true", default=True)

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("exec_command", nargs=argparse.REMAINDER)
    exec_parser.add_argument("--hosted", action="store_true")

    test = subparsers.add_parser("test")
    test.add_argument("test_command", nargs=argparse.REMAINDER)
    test.add_argument("--hosted", action="store_true")
    return parser


def api_base() -> str:
    return f"http://localhost:{os.getenv('API_HOST_PORT', '18000')}/api/v1"


def ensure_stack_running() -> None:
    try:
        get_json("/ready")
    except Exception:
        subprocess.run([str(START_SCRIPT)], cwd=ROOT_DIR, check=True)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"contexts": {}}
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def detect_repo() -> dict[str, Any]:
    cwd = str(Path.cwd().resolve())
    repo_root = None
    branch = None
    changed_files: list[str] = []
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for line in status_output.splitlines():
            if not line.strip():
                continue
            changed_files.append(line[3:].strip())
    except Exception:
        pass
    return {
        "cwd": cwd,
        "repo_root": repo_root,
        "branch": branch,
        "changed_files": changed_files[:8],
    }


def current_context_key() -> str:
    repo = detect_repo()
    return repo["repo_root"] or repo["cwd"]


def reset_context(key: str) -> None:
    state = load_state()
    state.setdefault("contexts", {}).pop(key, None)
    save_state(state)


def ensure_context(*, local_only: bool) -> dict[str, Any]:
    state = load_state()
    repo = detect_repo()
    key = repo["repo_root"] or repo["cwd"]
    existing = state.setdefault("contexts", {}).get(key, {})

    payload = {
        "cwd": repo["cwd"],
        "repo_root": repo["repo_root"],
        "branch": repo["branch"],
        "project_name": Path(key).name or "xyntra-project",
        "local_only": local_only,
        "project_id": existing.get("project_id"),
        "session_id": existing.get("session_id"),
    }
    context = post_json("/cli/context/ensure", payload)
    context["changed_files"] = repo["changed_files"]
    state["contexts"][key] = context
    save_state(state)
    return context


def interactive_chat(*, model: str, local_only: bool) -> None:
    context = ensure_context(local_only=local_only)
    print("Xyntra interactive chat")
    print(f"Project: {context['project_name']}")
    print(f"Repo: {context.get('repo_root') or context['cwd']}")
    print(f"Branch: {context.get('branch') or 'n/a'}")
    print(f"Model: {model}")
    print(
        "Slash commands: /help /status /files /sessions /switch <n|id> /branch [title] "
        "/model <name> /local on|off /exec <cmd> /test [cmd] /reset /exit"
    )

    current_model = model
    current_local_only = local_only

    while True:
        try:
            raw = input("\nxyntra> ").strip()
        except EOFError:
            print()
            return

        if not raw:
            continue
        if raw in {"/exit", "exit", "quit"}:
            return
        if raw == "/help":
            print(
                "Commands: /status /files /sessions /switch <n|id> /branch [title] "
                "/model <name> /local on|off /exec <cmd> /test [cmd] /reset /exit"
            )
            continue
        if raw == "/status":
            print_status()
            continue
        if raw == "/files":
            print(json.dumps(build_file_context(detect_repo()), indent=2))
            continue
        if raw == "/sessions":
            print_sessions(context)
            continue
        if raw.startswith("/switch "):
            target = raw.split(" ", 1)[1].strip()
            context = switch_session(context, target)
            print(f"Switched to session {context['session_id']}")
            continue
        if raw.startswith("/branch"):
            title = raw.split(" ", 1)[1].strip() if " " in raw else "CLI branch"
            context = branch_session(context, title)
            print(f"Branched to session {context['session_id']}")
            continue
        if raw.startswith("/model "):
            current_model = raw.split(" ", 1)[1].strip()
            print(f"Model set to {current_model}")
            continue
        if raw.startswith("/local "):
            value = raw.split(" ", 1)[1].strip().lower()
            current_local_only = value != "off"
            context = ensure_context(local_only=current_local_only)
            print(f"Routing mode: {'local-only' if current_local_only else 'mixed'}")
            continue
        if raw.startswith("/exec "):
            command = parse_command_text(raw.split(" ", 1)[1].strip())
            run_and_persist_command(context, command)
            continue
        if raw.startswith("/test"):
            command_text = raw.split(" ", 1)[1].strip() if " " in raw else ""
            command = (
                parse_command_text(command_text)
                if command_text
                else default_test_command(context)
            )
            run_and_persist_command(context, command)
            continue
        if raw == "/reset":
            reset_context(current_context_key())
            context = ensure_context(local_only=current_local_only)
            print("Context reset.")
            continue

        chat_once(prompt=raw, model=current_model, context=context, stream=True)


def print_status() -> None:
    ready = get_json("/ready")
    health = get_json("/health")
    state = load_state()
    context = state.get("contexts", {}).get(current_context_key())
    print(json.dumps({"ready": ready, "health": health, "context": context}, indent=2))


def print_sessions(context: dict[str, Any]) -> None:
    sessions = get_json(f"/projects/{context['project_id']}/sessions")
    for index, session in enumerate(sessions, start=1):
        print(
            f"{index}. {session['id']}  {session['title']}  "
            f"status={session['status']}"
        )


def switch_session(context: dict[str, Any], target: str) -> dict[str, Any]:
    sessions = get_json(f"/projects/{context['project_id']}/sessions")
    selected = None
    if target.isdigit():
        index = int(target) - 1
        if 0 <= index < len(sessions):
            selected = sessions[index]
    if selected is None:
        selected = next((item for item in sessions if item["id"] == target), None)
    if selected is None:
        raise SystemExit(f"Session not found: {target}")
    state = load_state()
    key = current_context_key()
    updated = dict(state["contexts"][key])
    updated["session_id"] = selected["id"]
    state["contexts"][key] = updated
    save_state(state)
    return updated


def branch_session(context: dict[str, Any], title: str) -> dict[str, Any]:
    messages = get_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages"
    )
    if not messages:
        raise SystemExit("Cannot branch an empty session.")
    last_message = messages[-1]
    branch = post_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/branch",
        {"message_id": last_message["id"], "title": title},
    )
    state = load_state()
    key = current_context_key()
    updated = dict(state["contexts"][key])
    updated["session_id"] = branch["id"]
    state["contexts"][key] = updated
    save_state(state)
    return updated


def build_file_context(repo: dict[str, Any]) -> dict[str, Any]:
    repo_root = repo["repo_root"]
    files: list[dict[str, str]] = []
    if repo_root is None:
        return {"repo_root": None, "branch": None, "files": files}
    root = Path(repo_root)
    for relative in repo["changed_files"][:5]:
        path = root / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        files.append(
            {
                "path": relative,
                "content": text[:8000],
            }
        )
    return {
        "repo_root": repo_root,
        "branch": repo["branch"],
        "files": files,
    }


def build_system_prompt(context: dict[str, Any]) -> str:
    repo = detect_repo()
    file_context = build_file_context(repo)
    parts = [
        "You are operating through Xyntra as a project-aware coding control plane.",
        f"cwd: {repo['cwd']}",
        f"repo_root: {repo.get('repo_root')}",
        f"branch: {repo.get('branch')}",
        f"changed_files: {repo.get('changed_files')}",
    ]
    if file_context["files"]:
        parts.append("Recent changed file context:")
        for item in file_context["files"]:
            parts.append(f"\n[path] {item['path']}\n{item['content']}")
    return "\n".join(parts)


def chat_once(*, prompt: str, model: str, context: dict[str, Any], stream: bool) -> str:
    system_prompt = build_system_prompt(context)
    messages = get_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages"
    )
    payload = {
        "model": model,
        "local_only": context.get("local_only", True),
        "stream": stream,
        "system_prompt": system_prompt,
        "metadata": {
            "project_id": context["project_id"],
            "session_id": context["session_id"],
            "cwd": context["cwd"],
            "repo_root": context.get("repo_root"),
            "branch": context.get("branch"),
            "terminal": os.getenv("TERM", "unknown"),
        },
        "messages": [
            {"role": item["role"], "content": item["content"]} for item in messages
        ]
        + [{"role": "user", "content": prompt}],
    }
    post_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages",
        {"role": "user", "content": prompt, "attachments": []},
    )
    if stream:
        content = stream_chat(payload)
    else:
        response = post_json("/chat", payload)
        content = response["response"]["content"]
    post_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages",
        {"role": "assistant", "content": content, "attachments": []},
    )
    state = load_state()
    key = current_context_key()
    if key in state.get("contexts", {}):
        state["contexts"][key]["last_model"] = model
        save_state(state)
    return content


def run_and_persist_command(context: dict[str, Any], command: list[str]) -> int:
    if not command:
        raise SystemExit("Command cannot be empty.")
    result = run_command(command, cwd=command_workdir(context))
    command_message, output_message, attachments = build_command_messages(result)
    save_session_message(
        context,
        role="user",
        content=command_message,
        attachments=[{"type": "cli_command_invocation", "argv": result["command"]}],
    )
    save_session_message(
        context,
        role="assistant",
        content=output_message,
        attachments=attachments,
    )
    return int(result["exit_code"])


def stream_chat(payload: dict[str, Any]) -> str:
    request = urllib.request.Request(
        f"{api_base()}/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    content_parts: list[str] = []
    with urllib.request.urlopen(request, timeout=120) as response:
        event_name = None
        for raw_line in response:
            line = raw_line.decode("utf-8").rstrip("\n")
            if not line:
                event_name = None
                continue
            if line.startswith("event: "):
                event_name = line.split(": ", 1)[1]
                continue
            if not line.startswith("data: "):
                continue
            payload = json.loads(line.split(": ", 1)[1])
            if event_name == "chunk":
                delta = payload.get("delta", "")
                content_parts.append(delta)
                print(delta, end="", flush=True)
        print()
    return "".join(content_parts)


def get_json(path: str) -> Any:
    with urllib.request.urlopen(f"{api_base()}{path}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict[str, Any]) -> Any:
    request = urllib.request.Request(
        f"{api_base()}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(body or str(exc)) from exc


def save_session_message(
    context: dict[str, Any],
    *,
    role: str,
    content: str,
    attachments: list[dict[str, Any]],
) -> None:
    post_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages",
        {"role": role, "content": content, "attachments": attachments},
    )


if __name__ == "__main__":
    main()

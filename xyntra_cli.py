from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import shutil
import socket
import subprocess
import time
import uuid
import webbrowser
from pathlib import Path
from typing import Any

import httpx

from services.contract_validation_service import contract_validation_service

ROOT_DIR = Path(__file__).resolve().parent
START_SCRIPT = ROOT_DIR / "scripts" / "start_xyntra.sh"
STATE_DIR = Path.home() / ".xyntra"
STATE_FILE = STATE_DIR / "cli_state.json"
DEFAULT_MODEL = "mistral"
DEFAULT_USER_EMAIL = "cli@xyntra.local"
DEFAULT_USER_NAME = "Xyntra CLI"
MARKETING_PATHS = {
    "landing": "/",
    "try-xyntra": "/try-xyntra",
    "pricing": "/pricing",
    "how-it-works": "/how-it-works",
    "demo": "/demo",
}
ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "accent": "\033[38;5;208m",
    "muted": "\033[38;5;244m",
}
LOGOMARK = [
    "            XX            ",
    "         XXXX  XXXX       ",
    "      XXXX        XXXX    ",
    "    XXXX            XXXX  ",
    "      XXXX        XXXX    ",
    "         XXXX  XXXX       ",
    "            XX            ",
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        run_start_script(seed_dev_data=args.seed)
        return

    if args.command == "api":
        import main as app_main

        app_main._run_api()
        return

    if args.command == "status":
        ensure_stack_running()
        print_status()
        return

    if args.command == "web":
        ensure_stack_running()
        open_marketing_site(args.page)
        return

    if args.command == "run":
        ensure_stack_running()
        result = asyncio.run(
            run_prompt(
                prompt=args.prompt,
                model=args.model,
                local_only=not args.hosted,
            )
        )
        print(result["response"]["content"])
        return

    if args.command == "validate-contract":
        ensure_stack_running()
        result = asyncio.run(
            validate_contract_file(
                source_path=args.source,
                major_version=args.major_version,
                output_dir=args.output_dir,
                chatgpt_model=args.chatgpt_model,
                kimi_model=args.kimi_model,
                claude_model=args.claude_model,
            )
        )
        print(
            json.dumps(
                {
                    "source_path": result.source_path,
                    "version": result.version,
                    "output_path": result.output_path,
                    "release_notes_path": result.release_notes_path,
                    "audit_path": result.audit_path,
                },
                indent=2,
            )
        )
        return

    if args.command == "reset-context":
        reset_context()
        print("Xyntra CLI context reset for this working directory.")
        return

    ensure_stack_running()
    try:
        asyncio.run(
            interactive_chat(
                model=args.model,
                local_only=not args.hosted,
                quiet_welcome=args.quiet_welcome,
            )
        )
    except KeyboardInterrupt:
        print("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xyntra")
    subparsers = parser.add_subparsers(dest="command")

    start = subparsers.add_parser("start", help="Start the full local stack.")
    start.add_argument(
        "--seed", action="store_true", help="Seed dev data after startup."
    )

    subparsers.add_parser(
        "status", help="Show stack readiness and current CLI context."
    )
    web = subparsers.add_parser("web", help="Open the local marketing site preview.")
    web.add_argument(
        "page",
        nargs="?",
        choices=sorted(MARKETING_PATHS),
        default="landing",
    )

    run = subparsers.add_parser(
        "run", help="Run a single prompt with retained project context."
    )
    run.add_argument("prompt")
    run.add_argument("--model", default=DEFAULT_MODEL)
    run.add_argument(
        "--hosted",
        action="store_true",
        help="Allow hosted routing instead of local-only.",
    )

    validate = subparsers.add_parser(
        "validate-contract",
        help="Refine a spec or coding contract through ChatGPT, Kimi, and Claude.",
    )
    validate.add_argument("source", help="Path to the spec or contract file.")
    validate.add_argument(
        "--major-version",
        type=int,
        default=1,
        help="Major version number for the generated contract output.",
    )
    validate.add_argument(
        "--output-dir",
        help="Optional output directory for generated contract versions.",
    )
    validate.add_argument(
        "--chatgpt-model",
        default="gpt-4o",
        help="OpenAI model to use for the ChatGPT refinement stage.",
    )
    validate.add_argument(
        "--kimi-model",
        help="Kimi model to use for the second refinement stage.",
    )
    validate.add_argument(
        "--claude-model",
        default="claude-sonnet-4-6",
        help="Anthropic model to use for the final refinement stage.",
    )

    subparsers.add_parser(
        "reset-context", help="Create a fresh CLI context for the current directory."
    )
    subparsers.add_parser(
        "api", help="Run only the FastAPI server in the current process."
    )

    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help="Default interactive model."
    )
    parser.add_argument("--quiet-welcome", action="store_true")
    parser.add_argument(
        "--hosted",
        action="store_true",
        help="Allow hosted routing instead of local-only.",
    )
    return parser


def api_base() -> str:
    explicit = os.getenv("XYNTRA_API_BASE")
    if explicit:
        return explicit.rstrip("/")
    return f"http://localhost:{os.getenv('API_HOST_PORT', '18000')}/api/v1"


def ui_base() -> str:
    return f"http://localhost:{os.getenv('UI_HOST_PORT', '4173')}"


def _docker_running() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _ensure_docker_running(timeout: int = 120) -> None:
    if _docker_running():
        return

    print("[xyntra] Docker Desktop is not running — starting it now...")
    try:
        subprocess.run(["open", "-a", "Docker"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[xyntra] Could not launch Docker Desktop automatically.")
        print("         Please open Docker Desktop manually and run xyntra again.")
        raise SystemExit(1)

    deadline = time.time() + timeout
    while time.time() < deadline:
        if _docker_running():
            print("\r\033[2K[xyntra] Docker Desktop is ready.", flush=True)
            return
        remaining = int(deadline - time.time())
        print(f"\r\033[2K[xyntra] Waiting for Docker Desktop... ({remaining}s)", end="", flush=True)
        time.sleep(3)

    print("\r\033[2K[xyntra] Docker Desktop did not become ready in time. Please try again.")
    raise SystemExit(1)


def run_start_script(*, seed_dev_data: bool) -> None:
    _ensure_docker_running()
    env = os.environ.copy()
    if seed_dev_data:
        env["SEED_DEV_DATA"] = "true"
    try:
        subprocess.run([str(START_SCRIPT)], cwd=ROOT_DIR, env=env, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"\n[xyntra] Stack startup failed (exit {exc.returncode}). Check Docker Desktop is healthy and try again.\n")
        raise SystemExit(1) from None


def ensure_stack_running() -> None:
    try:
        response = httpx.get(f"{api_base()}/ready", timeout=2.0)
        response.raise_for_status()
        return
    except Exception:
        run_start_script(seed_dev_data=False)


def ensure_ui_running() -> None:
    target = ui_base()
    deadline = time.time() + 90
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(target, timeout=5.0)
            response.raise_for_status()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise SystemExit(f"UI did not become ready: {last_error}")


def open_marketing_site(page: str) -> None:
    ensure_ui_running()
    target = f"{ui_base()}{MARKETING_PATHS[page]}"
    webbrowser.open(target)
    print(target)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"contexts": {}}
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def supports_color() -> bool:
    return os.getenv("TERM") not in {None, "", "dumb"} and os.isatty(1)


def style(text: str, *tokens: str) -> str:
    if not supports_color():
        return text
    prefix = "".join(ANSI[token] for token in tokens)
    return f"{prefix}{text}{ANSI['reset']}"


def centered_line(text: str, width: int | None = None) -> str:
    terminal_width = width or shutil.get_terminal_size((88, 20)).columns
    return text.center(terminal_width)


def repo_tip(context: dict[str, Any]) -> str:
    if (Path(context["cwd"]) / ".git").exists():
        return "Tip: start with /status, then ask: summarize this repo."
    return "Tip: start with /status or ask what this directory is for."


def suggested_first_request(context: dict[str, Any]) -> str:
    if (Path(context["cwd"]) / ".git").exists():
        return "explain what this repository does"
    return "explain what this directory contains"


def context_key() -> str:
    explicit = os.getenv("XYNTRA_CONTEXT_CWD")
    if explicit:
        return str(Path(explicit).resolve())
    return str(Path.cwd().resolve())


def reset_context() -> None:
    state = load_state()
    state.setdefault("contexts", {}).pop(context_key(), None)
    save_state(state)


def print_welcome_banner(
    *,
    context: dict[str, Any],
    model: str,
    local_only: bool,
    compact: bool,
) -> None:
    routing_label = "local-only" if local_only else "mixed"
    in_repo = (Path(context["cwd"]) / ".git").exists()
    first_move = "/status"
    first_request = suggested_first_request(context)
    print()
    print(style(centered_line("XYNTRA"), "accent", "bold"))
    for line in LOGOMARK:
        print(style(centered_line(line), "muted"))
    print(style(centered_line("Control Plane for the AI world"), "dim"))
    print()
    print(f"{style('Project:', 'bold')}   {context['project_name']}")
    print(f"{style('Directory:', 'bold')} {context['cwd']}")
    print(f"{style('Model:', 'bold')}     {model}")
    print(f"{style('Routing:', 'bold')}   {routing_label}")
    print()
    if compact:
        print(style("Quick start:", "bold"))
        print(f"- Plain-English request: {first_request}")
        print("- Contract refinement: /coding projects validation ./SPEC.md")
        print("- Reset this session context: /reset")
        print("- Show the full welcome again: /welcome full")
        print("- Leave Xyntra and return to your shell: Ctrl+C, /exit, exit, or bye")
        print(style(repo_tip(context), "dim"))
        return
    print(
        "You can either type a normal request in plain English or use a slash"
        " command."
    )
    print()
    print(style("Typical next moves:", "bold"))
    print(
        "- Ask it to do something: summarize this repo"
        if in_repo
        else "- Ask it to do something: explain what this directory contains"
    )
    print("- Inspect status: /status")
    print("- Reset this session context: /reset")
    print("- Exit: /exit")
    print()
    print(style("Sensible first commands:", "bold"))
    print(f"- {first_move}")
    print(f"- {first_request}")
    print("- /coding projects validation ./SPEC.md")
    print("- /reset if you want a fresh session for this directory")
    print("- Ctrl+C, /exit, exit, or bye to leave Xyntra and return to your shell")
    print()
    print(style(repo_tip(context), "dim"))


def set_welcome_mode(key: str, mode: str) -> None:
    state = load_state()
    if key in state.get("contexts", {}):
        state["contexts"][key]["welcome_mode"] = mode
        save_state(state)


async def interactive_chat(
    *, model: str, local_only: bool, quiet_welcome: bool
) -> None:
    context = await ensure_cli_context()
    state = load_state()
    key = context_key()
    stored_context = state.get("contexts", {}).get(key, {})
    welcome_mode = stored_context.get("welcome_mode", "auto")
    compact = bool(stored_context.get("welcome_seen"))
    if welcome_mode == "full":
        compact = False
    if welcome_mode == "compact":
        compact = True
    if not quiet_welcome:
        print_welcome_banner(
            context=context,
            model=model,
            local_only=local_only,
            compact=compact,
        )
    if key in state.get("contexts", {}):
        state["contexts"][key]["welcome_seen"] = True
        save_state(state)

    while True:
        try:
            prompt = input("\nxyntra> ").strip()
        except KeyboardInterrupt:
            print()
            break
        except EOFError:
            print()
            break

        if not prompt:
            continue
        if prompt in {"/exit", "exit", "quit", "bye"}:
            break
        if prompt == "/status":
            print_status()
            continue
        if prompt == "/reset":
            reset_context()
            context = await ensure_cli_context()
            print("Context reset.")
            continue
        if prompt.startswith("/coding projects validation"):
            try:
                summary = await handle_contract_validation_command(prompt)
            except ValueError as exc:
                print(str(exc))
                continue
            print(summary)
            continue
        if prompt.startswith("/welcome "):
            value = prompt.split(" ", 1)[1].strip().lower()
            if value not in {"full", "compact"}:
                print("Usage: /welcome <full|compact>")
                continue
            set_welcome_mode(key, value)
            print(f"Welcome mode set to {value}.")
            continue

        result = await run_prompt(prompt=prompt, model=model, local_only=local_only)
        print(result["response"]["content"])


async def run_prompt(*, prompt: str, model: str, local_only: bool) -> dict[str, Any]:
    context = await ensure_cli_context()
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{api_base()}/chat",
            json={
                "model": model,
                "local_only": local_only,
                "metadata": {
                    "project_id": context["project_id"],
                    "session_id": context["session_id"],
                    "cwd": context["cwd"],
                    "hostname": socket.gethostname(),
                    "terminal": os.getenv("TERM", "unknown"),
                },
                "messages": await build_messages(context["project_id"], context["session_id"], prompt),
            },
        )
        response.raise_for_status()
        payload = response.json()

    await append_message(context["project_id"], context["session_id"], "user", prompt)
    await append_message(context["project_id"], context["session_id"], "assistant", payload["response"]["content"])

    state = load_state()
    stored = state.setdefault("contexts", {}).setdefault(context_key(), {})
    stored["last_model"] = model
    stored["local_only"] = local_only
    save_state(state)
    return payload


async def ensure_cli_context() -> dict[str, Any]:
    state = load_state()
    contexts = state.setdefault("contexts", {})
    key = context_key()
    stored = contexts.get(key)

    cwd = key
    project_name = Path(cwd).name or "xyntra-project"

    branch: str | None = None
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=3,
        )
        if r.returncode == 0:
            branch = r.stdout.strip()
    except Exception:
        pass

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{api_base()}/cli/context/ensure",
            json={
                "cwd": cwd,
                "project_name": project_name,
                "branch": branch,
                "local_only": True,
                "project_id": stored.get("project_id") if stored else None,
                "session_id": stored.get("session_id") if stored else None,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    context = {
        "cwd": cwd,
        "project_id": data["project_id"],
        "project_name": data["project_name"],
        "session_id": data["session_id"],
        "user_id": data["user_id"],
        "last_model": stored.get("last_model", DEFAULT_MODEL) if stored else DEFAULT_MODEL,
        "local_only": True,
    }
    contexts[key] = context
    save_state(state)
    return context


async def build_messages(project_id: str, session_id: str, prompt: str) -> list[dict[str, str]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{api_base()}/projects/{project_id}/sessions/{session_id}/messages"
            )
            resp.raise_for_status()
            history = resp.json()
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
    except Exception:
        messages = []
    messages.append({"role": "user", "content": prompt})
    return messages


async def append_message(project_id: str, session_id: str, role: str, content: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{api_base()}/projects/{project_id}/sessions/{session_id}/messages",
                json={"role": role, "content": content},
            )
    except Exception:
        pass




async def validate_contract_file(
    *,
    source_path: str,
    major_version: int,
    output_dir: str | None,
    chatgpt_model: str,
    kimi_model: str | None,
    claude_model: str,
):
    return await contract_validation_service.validate_contract(
        source_path=source_path,
        major_version=major_version,
        output_dir=output_dir,
        chatgpt_model=chatgpt_model,
        kimi_model=kimi_model,
        claude_model=claude_model,
    )


async def handle_contract_validation_command(prompt: str) -> str:
    prefix = "/coding projects validation"
    remainder = prompt[len(prefix) :].strip()
    if not remainder:
        raise ValueError(
            "Usage: /coding projects validation <path> [--major-version N]"
        )

    tokens = shlex.split(remainder)
    source_path = tokens[0]
    major_version = 1
    output_dir: str | None = None
    chatgpt_model = "gpt-4o"
    kimi_model: str | None = None
    claude_model = "claude-sonnet-4-6"

    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--major-version":
            index += 1
            if index >= len(tokens):
                raise ValueError("Missing value for --major-version.")
            major_version = int(tokens[index])
        elif token == "--output-dir":
            index += 1
            if index >= len(tokens):
                raise ValueError("Missing value for --output-dir.")
            output_dir = tokens[index]
        elif token == "--chatgpt-model":
            index += 1
            if index >= len(tokens):
                raise ValueError("Missing value for --chatgpt-model.")
            chatgpt_model = tokens[index]
        elif token == "--kimi-model":
            index += 1
            if index >= len(tokens):
                raise ValueError("Missing value for --kimi-model.")
            kimi_model = tokens[index]
        elif token == "--claude-model":
            index += 1
            if index >= len(tokens):
                raise ValueError("Missing value for --claude-model.")
            claude_model = tokens[index]
        else:
            raise ValueError(f"Unsupported option: {token}")
        index += 1

    result = await validate_contract_file(
        source_path=source_path,
        major_version=major_version,
        output_dir=output_dir,
        chatgpt_model=chatgpt_model,
        kimi_model=kimi_model,
        claude_model=claude_model,
    )
    return (
        f"Major contract version {result.version} created.\n"
        f"Contract: {result.output_path}\n"
        f"What's included: {result.release_notes_path}\n"
        f"Audit: {result.audit_path}"
    )


def print_status() -> None:
    ready = httpx.get(f"{api_base()}/ready", timeout=5.0)
    health = httpx.get(f"{api_base()}/health", timeout=5.0)
    context = load_state().get("contexts", {}).get(context_key())
    print(
        json.dumps(
            {
                "ready": ready.json(),
                "health": health.json(),
                "context": context,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

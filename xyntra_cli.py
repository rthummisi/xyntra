from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import socket
import subprocess
import time
import uuid
import webbrowser
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.message import Message
from models.project import Project
from models.session import Session
from models.user import User
from services.project_service import project_service
from services.session_service import session_service

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


def run_start_script(*, seed_dev_data: bool) -> None:
    env = os.environ.copy()
    if seed_dev_data:
        env["SEED_DEV_DATA"] = "true"
    subprocess.run([str(START_SCRIPT)], cwd=ROOT_DIR, env=env, check=True)


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
                "messages": await build_messages(context["session_id"], prompt),
            },
        )
        response.raise_for_status()
        payload = response.json()

    await append_message(context["session_id"], "user", prompt)
    await append_message(
        context["session_id"], "assistant", payload["response"]["content"]
    )

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

    async with AsyncSessionLocal() as db:
        user = await ensure_cli_user(db)

        if stored:
            project = await db.get(Project, uuid.UUID(stored["project_id"]))
            session = await db.get(Session, uuid.UUID(stored["session_id"]))
            if project is not None and session is not None:
                stored["project_name"] = project.name
                save_state(state)
                return stored

        cwd = key
        project_name = Path(cwd).name or "xyntra-project"
        project = await project_service.create_project(
            db,
            owner_id=user.id,
            name=f"{project_name}",
            description=f"CLI context for {cwd}",
            local_only=True,
        )
        session = await session_service.create_session(
            db,
            project_id=project.id,
            user_id=user.id,
            title=f"CLI session for {project_name}",
        )
        context = {
            "cwd": cwd,
            "project_id": str(project.id),
            "project_name": project.name,
            "session_id": str(session.id),
            "user_id": str(user.id),
            "last_model": DEFAULT_MODEL,
            "local_only": True,
        }
        contexts[key] = context
        save_state(state)
        return context


async def ensure_cli_user(db) -> User:
    result = await db.execute(select(User).where(User.email == DEFAULT_USER_EMAIL))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(
        email=DEFAULT_USER_EMAIL,
        display_name=DEFAULT_USER_NAME,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def build_messages(session_id: str, prompt: str) -> list[dict[str, str]]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == uuid.UUID(session_id))
            .order_by(Message.sequence_number.asc())
        )
        history = list(result.scalars().all())
    messages = [{"role": item.role, "content": item.content} for item in history]
    messages.append({"role": "user", "content": prompt})
    return messages


async def append_message(session_id: str, role: str, content: str) -> None:
    async with AsyncSessionLocal() as db:
        await session_service.add_message(
            db,
            session_id=uuid.UUID(session_id),
            role=role,
            content=content,
            attachments=[],
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

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import time
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
DEFAULT_MODEL = "qwen2.5-coder:7b"
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
    "ok": "\033[38;5;71m",
    "warn": "\033[38;5;214m",
    "err": "\033[38;5;196m",
    "cyan": "\033[38;5;75m",
    "purple": "\033[38;5;141m",
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
        env = os.environ.copy()
        if args.seed:
            env["SEED_DEV_DATA"] = "true"
        subprocess.run([str(START_SCRIPT)], cwd=ROOT_DIR, env=env, check=True)
        return

    ensure_stack_running()

    if args.command == "status":
        print_status()
        return

    if args.command == "web":
        open_marketing_site(args.page)
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

    try:
        interactive_chat(
            model=args.model,
            local_only=not args.hosted,
            quiet_welcome=args.quiet_welcome,
        )
    except KeyboardInterrupt:
        print("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xyntra")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--hosted", action="store_true")
    parser.add_argument("--quiet-welcome", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    start = subparsers.add_parser("start")
    start.add_argument("--seed", action="store_true")

    subparsers.add_parser("status")
    web_parser = subparsers.add_parser("web")
    web_parser.add_argument(
        "page",
        nargs="?",
        choices=sorted(MARKETING_PATHS),
        default="landing",
    )
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


def ui_base() -> str:
    return f"http://localhost:{os.getenv('UI_HOST_PORT', '4173')}"


def ensure_docker_running() -> None:
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return
    print("Docker is not running. Starting Docker Desktop...")
    subprocess.run(["open", "-a", "Docker"], check=True)
    deadline = time.time() + 60
    while time.time() < deadline:
        r = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if r.returncode == 0:
            return
        time.sleep(2)
    raise SystemExit("Docker Desktop did not start within 60 seconds.")


def ensure_stack_running() -> None:
    ensure_docker_running()
    try:
        get_json("/ready")
    except Exception:
        subprocess.run([str(START_SCRIPT)], cwd=ROOT_DIR, check=True)


def ensure_ui_running() -> None:
    target = ui_base()
    deadline = time.time() + 90
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(target, timeout=5):
                return
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise SystemExit(f"UI did not become ready: {last_error}")


def open_marketing_site(page: str) -> None:
    ensure_stack_running()
    ensure_ui_running()
    target = f"{ui_base()}{MARKETING_PATHS[page]}"
    open_command = "open" if os.uname().sysname == "Darwin" else "xdg-open"
    try:
        subprocess.Popen(
            [open_command, target],
            cwd=ROOT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    print(target)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"contexts": {}}
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def remember_repo(name: str, path: str) -> None:
    """Persist a project name → absolute path mapping so xyntra never asks again."""
    state = load_state()
    state.setdefault("known_repos", {})[name.lower()] = path
    save_state(state)


def recall_repo(name: str) -> str | None:
    """Return the saved path for a project name, if known."""
    return load_state().get("known_repos", {}).get(name.lower())


def save_feedback(lesson: str) -> None:
    """Persist a lesson learned from user corrections for future sessions."""
    state = load_state()
    feedbacks: list[str] = state.setdefault("learned_feedback", [])
    if lesson not in feedbacks:
        feedbacks.append(lesson)
        if len(feedbacks) > 20:
            feedbacks.pop(0)
    save_state(state)


def load_feedback() -> list[str]:
    return load_state().get("learned_feedback", [])


_CORRECTION_PHRASES = [
    "that's wrong", "that is wrong", "not what i asked", "i asked you to",
    "don't give me", "stop giving", "you're supposed to", "you were supposed to",
    "not guide me", "just point out", "not guide", "crap again",
    "same crap", "wrong answer", "didn't ask for that",
]


def _is_user_correction(prompt: str) -> bool:
    lower = prompt.lower()
    return any(phrase in lower for phrase in _CORRECTION_PHRASES)


def _extract_correction_lesson(correction: str, last_response: str) -> str:
    """Turn a user correction into a concise lesson string."""
    correction = correction.strip()[:200]
    return f"When asked a task and I gave generic advice, user said: '{correction}'. Always use tools to read actual files — never give generic bullet-point guidance."


_GENERIC_SIGNALS = [
    # generic guidance patterns
    "you can follow these steps",
    "here are some steps",
    "to identify the missing",
    "you would need to",
    "as an ai language model",
    "i don't have the capability",
    "i cannot directly access",
    "you should review",
    "access the repository and review",
    "by following these steps",
    "feel free to provide more details",
    "if you have access to",
    "you can look for",
    "i can suggest",
    # hedging / refusal to commit
    "it's impossible to say",
    "without running the code",
    "without more context",
    "to get a better understanding",
    "to get a clearer picture",
    "you can call",           # model telling USER to run tools
    "you could call",
    "you would need to call",
    "for more information",
    "i recommend checking",
    "i would recommend",
    "consider checking",
    "it would be worth",
    "it may be worth",
]


def _is_generic_response(content: str) -> bool:
    """True when the model hedged or gave generic advice instead of direct findings."""
    lower = content.lower()
    hits = sum(1 for s in _GENERIC_SIGNALS if s in lower)
    return hits >= 1  # one hedge phrase is already a failure


def supports_color() -> bool:
    return os.getenv("TERM") not in {None, "", "dumb"} and os.isatty(1)


def style(text: str, *tokens: str) -> str:
    if not supports_color():
        return text
    prefix = "".join(ANSI[token] for token in tokens)
    return f"{prefix}{text}{ANSI['reset']}"


def _spin(label: str):
    """Start an animated braille spinner. Returns a stop() callable that
    waits for the thread to finish before returning, so callers can safely
    print immediately after."""
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    stop_event = threading.Event()
    width = len(label) + 6

    def _run() -> None:
        i = 0
        while not stop_event.is_set():
            frame = FRAMES[i % len(FRAMES)]
            sys.stdout.write(f"\r{style(frame, 'cyan')} {style(label, 'dim')}  ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
        sys.stdout.write("\r" + " " * width + "\r")
        sys.stdout.flush()

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    def stop() -> None:
        stop_event.set()
        t.join(timeout=0.3)

    return stop


def centered_line(text: str, width: int | None = None) -> str:
    terminal_width = width or shutil.get_terminal_size((88, 20)).columns
    return text.center(terminal_width)


def repo_tip(context: dict[str, Any]) -> str:
    changed_files = context.get("changed_files") or []
    if context.get("repo_root") and changed_files:
        return (
            "Tip: run /files to inspect the "
            f"{len(changed_files)} changed files in scope."
        )
    if context.get("repo_root"):
        return "Tip: start with /status, then ask: summarize this repo."
    return "Tip: start with /status or /exec pwd to ground the session."


def suggested_first_request(context: dict[str, Any]) -> str:
    changed_files = context.get("changed_files") or []
    if context.get("repo_root") and changed_files:
        return "review the recent changed files and tell me the highest-risk area"
    if context.get("repo_root"):
        return "explain what this repository does"
    return "explain what this directory contains"


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
    merged = dict(existing)
    merged.update(context)
    merged["changed_files"] = repo["changed_files"]
    state["contexts"][key] = merged
    save_state(state)
    return merged


def print_welcome_banner(
    *,
    context: dict[str, Any],
    model: str,
    local_only: bool,
    compact: bool,
) -> None:
    repo_label = context.get("repo_root") or context["cwd"]
    branch_label = context.get("branch") or "n/a"
    routing_label = "local-only" if local_only else "mixed"
    first_move = "/status"
    first_request = suggested_first_request(context)
    print()
    print(style(centered_line("XYNTRA"), "accent", "bold"))
    for line in LOGOMARK:
        print(style(centered_line(line), "muted"))
    print(style(centered_line("Control Plane for the AI world"), "dim"))
    print()
    print(f"{style('Project:', 'bold')} {context['project_name']}")
    print(f"{style('Repo:', 'bold')}    {repo_label}")
    print(f"{style('Branch:', 'bold')}  {branch_label}")
    print(f"{style('Model:', 'bold')}   {model}")
    print(f"{style('Routing:', 'bold')} {routing_label}")
    print()
    if compact:
        print(style("Quick start:", "bold"))
        print(f"- Ask anything: {first_request}")
        print("- All commands: /help")
        print("- Return to shell: /exit  or  type exit  or  Ctrl+C when idle")
        print("- Cancel a running task: Ctrl+C once (stays in xyntra)")
        print(style(repo_tip(context), "dim"))
        return
    print("Type a plain-English request or a slash command.")
    print()
    print(style("Get started:", "bold"))
    if context.get("repo_root"):
        print(f"- {first_request}")
        print("- review this repo for bugs")
        print("- /status  — stack health")
        print("- /files   — files in context")
    else:
        print(f"- {first_request}")
        print("- /status  — stack health")
        print("- /exec pwd  — run a shell command")
    print()
    print(style("Useful commands:", "bold"))
    print("- /models              — see installed models and what each handles")
    print("- /history             — recent conversation")
    print("- /undo                — restore last overwritten file")
    print("- /model <name>        — pin a specific model")
    print("- /reset               — clear session context")
    print("- /help                — full command list")
    print()
    print(style("Leaving xyntra:", "bold"))
    print("- Ctrl+C when idle, /exit, exit, or bye  → returns to your shell")
    print("- Ctrl+C during a running task            → cancels the task, stays in xyntra")
    print()
    print(style(repo_tip(context), "dim"))


def set_welcome_mode(context_key_value: str, mode: str) -> None:
    state = load_state()
    if context_key_value in state.get("contexts", {}):
        state["contexts"][context_key_value]["welcome_mode"] = mode
        save_state(state)


_IMAGE_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # checked further below
]


def _image_media_type(path: Path) -> str | None:
    try:
        header = path.read_bytes()[:12]
    except Exception:
        return None
    for sig, mime in _IMAGE_SIGNATURES:
        if header.startswith(sig):
            if mime == "image/webp" and b"WEBP" not in header:
                continue
            return mime
    return None


def _load_attachment(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        print(f"File not found: {path}")
        return None
    mime = _image_media_type(path)
    if mime:
        data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        return {
            "type": "image",
            "path": str(path),
            "media_type": mime,
            "data": data,
        }
    try:
        content = path.read_text(errors="replace")
        return {"type": "text_file", "path": str(path), "content": content}
    except Exception as exc:
        print(f"Could not read file: {exc}")
        return None


def _clipboard_attachment() -> dict[str, Any] | None:
    if os.uname().sysname != "Darwin":
        print("/paste is only supported on macOS.")
        return None
    tmp = Path(tempfile.mktemp(suffix=".png"))
    script = (
        f'set imgData to (the clipboard as «class PNGf»)\n'
        f'set f to open for access POSIX file "{tmp}" with write permission\n'
        f'write imgData to f\n'
        f'close access f'
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
    )
    if result.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
        data = base64.standard_b64encode(tmp.read_bytes()).decode("ascii")
        tmp.unlink(missing_ok=True)
        return {"type": "image", "path": "<clipboard>", "media_type": "image/png", "data": data}
    tmp.unlink(missing_ok=True)
    pb = subprocess.run(["pbpaste"], capture_output=True, text=True)
    if pb.returncode == 0 and pb.stdout.strip():
        return {"type": "text_file", "path": "<clipboard>", "content": pb.stdout}
    print("Clipboard is empty or contains unsupported content.")
    return None


def _describe_attachment(att: dict[str, Any]) -> str:
    label = Path(att["path"]).name or att["path"]
    if att["type"] == "image":
        return f"[image: {label}]"
    lines = att["content"].count("\n") + 1
    return f"[text: {label}, {lines} lines]"


def read_prompt(indicator: str) -> str:
    """Read user input.  Pasted text (which contains embedded newlines) is
    accumulated without triggering submission; only an explicit Enter press
    (outside of a paste) submits the input.  Falls back to the simple
    select-drain approach when the terminal is not a real TTY."""
    try:
        import termios, tty as _tty
        if not os.isatty(sys.stdin.fileno()):
            raise OSError("not a tty")
    except (ImportError, OSError):
        return _read_prompt_select(indicator)
    return _read_prompt_bracketed(indicator)


def _read_prompt_select(indicator: str) -> str:
    first = input(indicator)
    lines = [first]
    try:
        while select.select([sys.stdin], [], [], 0.5)[0]:
            extra = sys.stdin.readline()
            if not extra:
                break
            lines.append(extra.rstrip("\n"))
    except Exception:
        pass
    return "\n".join(lines)


_paste_counter = 0  # session-level paste counter shown in the summary tag


def _read_prompt_bracketed(indicator: str) -> str:
    global _paste_counter
    import termios, tty as _tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    # Enable bracketed-paste mode: ESC[200~ opens paste, ESC[201~ closes it.
    sys.stdout.write("\033[?2004h" + indicator)
    sys.stdout.flush()

    chars: list[str] = []
    in_paste = False
    paste_start: int = 0   # index into chars where current paste began
    paste_open: str = ""   # the opening part of the tag (before line count)

    try:
        _tty.setraw(fd)
        pending = ""
        while True:
            select.select([fd], [], [])
            pending += os.read(fd, 256).decode("utf-8", errors="replace")

            while pending:
                if pending.startswith("\x1b[200~"):
                    in_paste = True
                    paste_start = len(chars)
                    _paste_counter += 1
                    # Write opening half of tag — line count appended when paste ends.
                    paste_open = f"[Pasted text #{_paste_counter}"
                    sys.stdout.write(paste_open)
                    sys.stdout.flush()
                    pending = pending[6:]
                elif pending.startswith("\x1b[201~"):
                    in_paste = False
                    # Append line count to close the tag — no cursor movement needed.
                    lines = sum(1 for ch in chars[paste_start:] if ch == "\n")
                    sys.stdout.write(f" +{lines} lines]")
                    sys.stdout.flush()
                    pending = pending[6:]
                elif pending.startswith("\x1b") and len(pending) < 6:
                    if select.select([fd], [], [], 0.05)[0]:
                        pending += os.read(fd, 64).decode("utf-8", errors="replace")
                    else:
                        pending = pending[1:]
                elif pending.startswith("\x1b"):
                    pending = pending[1:]
                else:
                    c = pending[0]
                    pending = pending[1:]
                    if c == "\x03":
                        raise KeyboardInterrupt
                    elif c == "\x04":
                        if not chars:
                            raise EOFError
                        sys.stdout.write("\r\n")
                        sys.stdout.flush()
                        return "".join(chars)
                    elif c in ("\r", "\n"):
                        if in_paste:
                            chars.append("\n")   # accumulate silently — no screen output
                        else:
                            sys.stdout.write("\r\n")
                            sys.stdout.flush()
                            return "".join(chars)
                    elif c == "\x7f":  # Backspace
                        if paste_open and len(chars) > paste_start:
                            # Discard entire paste block — not worth editing individual chars.
                            del chars[paste_start:]
                            tag_len = len(paste_open) + len(f" +XX lines]")
                            sys.stdout.write("\b" * tag_len + " " * tag_len + "\b" * tag_len)
                            sys.stdout.flush()
                            paste_open = ""
                        elif chars:
                            chars.pop()
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    elif in_paste:
                        chars.append(c)   # accumulate silently
                    else:
                        chars.append(c)
                        sys.stdout.write(c)
                        sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[?2004l")
        sys.stdout.flush()
    return "".join(chars)


def interactive_chat(*, model: str, local_only: bool, quiet_welcome: bool) -> None:
    context = ensure_context(local_only=local_only)
    state = load_state()
    key = current_context_key()
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

    current_model = model
    current_local_only = local_only
    pending_attachments: list[dict[str, Any]] = []
    pending_repo_query: str | None = None   # query waiting for a path reply
    last_response: str = ""                  # last model response (for feedback capture)

    def _prompt_str() -> str:
        task_model, _ = _pick_model("read", current_model)
        m = task_model.split(":")[0] if ":" in task_model else task_model
        base = f"\nxyntra [{m}]"
        if pending_attachments:
            base += f" [{len(pending_attachments)} attached]"
        return base + "> "

    while True:
        try:
            raw = read_prompt(_prompt_str()).strip()
        except KeyboardInterrupt:
            print()
            return
        except EOFError:
            print()
            return

        if not raw:
            continue
        if raw in {"/exit", "exit", "quit", "bye"}:
            return
        if raw == "/help":
            print(
                "Commands:\n"
                "  /history              — show recent conversation\n"
                "  /models               — list installed models and auto-selection\n"
                "  /undo                 — restore last overwritten file\n"
                "  /feedback             — show learned feedback lessons\n"
                "  /model <name>         — pin model for this session\n"
                "  /local on|off         — toggle local-only routing\n"
                "  /status               — stack health\n"
                "  /files                — show repo file context\n"
                "  /sessions             — list sessions\n"
                "  /switch <n|id>        — switch session\n"
                "  /branch [title]       — branch current session\n"
                "  /exec <cmd>           — run shell command\n"
                "  /test [cmd]           — run tests\n"
                "  /attach <path>        — attach file\n"
                "  /paste                — attach clipboard\n"
                "  /attachments          — list attachments\n"
                "  /clear-attachments    — clear attachments\n"
                "  /reset                — clear session context\n"
                "  /exit                 — quit"
            )
            continue
        if raw.startswith("/attach "):
            path = Path(raw.split(" ", 1)[1].strip()).expanduser().resolve()
            att = _load_attachment(path)
            if att:
                pending_attachments.append(att)
                print(f"Attached {_describe_attachment(att)}")
            continue
        if raw == "/paste":
            att = _clipboard_attachment()
            if att:
                pending_attachments.append(att)
                print(f"Attached {_describe_attachment(att)}")
            continue
        if raw == "/attachments":
            if not pending_attachments:
                print("No pending attachments.")
            for i, att in enumerate(pending_attachments, 1):
                print(f"  {i}. {_describe_attachment(att)}")
            continue
        if raw == "/clear-attachments":
            pending_attachments.clear()
            print("Attachments cleared.")
            continue
        if raw == "/ping":
            print("pong")
            continue
        if raw == "/history":
            _print_history(context)
            continue
        if raw == "/models":
            _print_models(current_model)
            continue
        if raw == "/undo":
            path = _undo_last_write()
            if path:
                print(style(f"  ✓ Restored {path}", "ok"))
            else:
                print("  Nothing to undo.")
            continue
        if raw == "/feedback":
            _print_feedback()
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
        if raw.startswith("/welcome "):
            value = raw.split(" ", 1)[1].strip().lower()
            if value not in {"full", "compact"}:
                print("Usage: /welcome <full|compact>")
                continue
            set_welcome_mode(key, value)
            print(f"Welcome mode set to {value}.")
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

        # ── Paste-only: no verb, no question — ask what to do ────────────────
        if raw.startswith("[Pasted text #") and raw.endswith("]"):
            print("  What do you want to do with this? (e.g. review it, fix it, explain it)")
            continue

        # ── Detect user corrections and save as feedback ──────────────────────
        if _is_user_correction(raw) and last_response:
            lesson = _extract_correction_lesson(raw, last_response)
            save_feedback(lesson)
            print(style("  ✓ Got it — I'll remember that for next time.", "ok"))

        # ── If we asked for a path, next input IS the path ────────────────────
        if pending_repo_query is not None:
            resolved = _resolve_path_reply(raw)
            if resolved:
                repo_name = _foreign_repo_name(pending_repo_query) or Path(resolved).name
                remember_repo(repo_name, resolved)
                remember_repo(Path(resolved).name.lower(), resolved)
                print(style(f"  ✓ Saved — {repo_name} → {resolved}", "ok"))
                saved_query = pending_repo_query
                pending_repo_query = None
                mode = _prompt_mode(saved_query)
                task_model, auto = _pick_model(mode, current_model)
                if auto:
                    print(style(f"  ◎ Auto-selected model: {task_model} ({mode} task)", "muted"))
                try:
                    last_response = _run_agent(
                        prompt=saved_query,
                        mode=mode,
                        current_model=task_model,
                        context=context,
                        override_work_dir=resolved,
                    )
                except KeyboardInterrupt:
                    print(style("\n  ✗ Cancelled — Ctrl+C again to exit xyntra.", "warn"))
            else:
                print(style(f"  ✗ Path not found: {raw!r}", "err"))
                print("  Please provide the full absolute path.")
            continue

        # ── Normal routing ────────────────────────────────────────────────────
        mode = _prompt_mode(raw)
        task_model, auto = _pick_model(mode, current_model)
        if auto:
            print(style(f"  ◎ {task_model}  [{mode}]", "muted"))

        if mode in {"write", "read"}:
            mentioned_path = _extract_path_from_prompt(raw)
            if mentioned_path and raw.strip().startswith("/"):
                remember_repo(Path(mentioned_path).name, mentioned_path)
            if not mentioned_path:
                repo_name = _foreign_repo_name(raw)
                if repo_name:
                    mentioned_path = recall_repo(repo_name)
            if not mentioned_path and _is_foreign_repo(raw, context):
                repo_name = _foreign_repo_name(raw) or "that repo"
                print(
                    f"\n  I don't have the location of {repo_name!r}.\n"
                    "  What's the full path? (e.g. /Users/you/projects/growthos)"
                )
                pending_repo_query = raw
            else:
                try:
                    last_response = _run_agent(
                        prompt=raw,
                        mode=mode,
                        current_model=task_model,
                        context=context,
                        override_work_dir=mentioned_path,
                    )
                except KeyboardInterrupt:
                    print(style("\n  ✗ Cancelled — Ctrl+C again to exit xyntra.", "warn"))
        else:
            last_response = ""
            try:
                stream_chat(_build_chat_payload(raw, task_model, context, conversational=_is_conversational(raw)))
            except KeyboardInterrupt:
                print()
        pending_attachments = []


def _print_history(context: dict[str, Any]) -> None:
    history = get_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages"
    )
    if not history:
        print("  No history yet.")
        return
    for msg in history[-20:]:
        role = msg.get("role", "")
        content = str(msg.get("content", ""))[:300].replace("\n", " ")
        icon = "you" if role == "user" else " ai"
        print(f"  {style(icon, 'muted')}  {content}")


def _print_models(current: str) -> None:
    available = _available_ollama_models()
    if not available:
        print("  Ollama not reachable.")
        return
    chat_m, _ = _pick_model("chat", current)
    read_m, _ = _pick_model("read", current)
    write_m, _ = _pick_model("write", current)
    print(f"  Installed ({len(available)} models):")
    for m in sorted(available):
        tags = []
        if m == chat_m:
            tags.append("chat")
        if m == read_m:
            tags.append("read")
        if m == write_m:
            tags.append("write")
        if m == current:
            tags.append("pinned")
        label = f"  [{', '.join(tags)}]" if tags else ""
        print(f"    {m}{style(label, 'cyan')}")


# Undo stack: list of (path, original_bytes) for last 5 write_file calls
_write_undo_stack: list[tuple[str, bytes]] = []


def _record_undo(path: str, original: bytes) -> None:
    _write_undo_stack.append((path, original))
    if len(_write_undo_stack) > 5:
        _write_undo_stack.pop(0)


def _undo_last_write() -> str | None:
    if not _write_undo_stack:
        return None
    path, original = _write_undo_stack.pop()
    Path(path).write_bytes(original)
    return path


def _print_feedback() -> None:
    feedbacks = load_feedback()
    if not feedbacks:
        print("  No lessons learned yet.")
        return
    print(f"  {len(feedbacks)} lessons learned:")
    for i, f in enumerate(feedbacks, 1):
        print(f"  {i}. {f[:120]}")


_DANGEROUS_BASH = [
    "rm -rf", "rm -r /", "git reset --hard", "git clean -f",
    "drop table", "truncate ", "> /dev/", "mkfs", "dd if=",
    "chmod -R 777", ":(){:|:&};:", "fork bomb",
]


def _is_dangerous_bash(command: str) -> bool:
    lower = command.lower()
    return any(d in lower for d in _DANGEROUS_BASH)


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


AGENT_TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the filesystem. Use this to understand existing code before editing.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Absolute or repo-relative file path"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file with new content. Use this to create or update code.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute or repo-relative file path to write"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "bash",
        "description": "Run a shell command (tests, installs, git, etc.) and return stdout+stderr.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string", "description": "Working directory (optional, defaults to repo root)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files and directories at a path.",
        "parameters": {
            "type": "object",
            "properties": {"directory": {"type": "string", "description": "Directory path to list"}},
            "required": ["directory"],
        },
    },
    {
        "name": "find_files",
        "description": "Find files matching a glob pattern inside the repo.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern e.g. '**/*.ts'"},
                "root": {"type": "string", "description": "Root directory (optional)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep_files",
        "description": "Search for a text pattern inside files. Returns matching lines with file:line references.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search string or regex"},
                "glob": {"type": "string", "description": "File filter e.g. '*.py' (optional, default all)"},
                "root": {"type": "string", "description": "Root directory to search (optional)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "git",
        "description": "Run a read-only git command (log, diff, status, show, branch, blame). Never modifies the repo.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "git subcommand + args e.g. 'log --oneline -10' or 'diff HEAD~1'"},
            },
            "required": ["command"],
        },
    },
]

# Read-only subset — used for analysis/review queries so the model can't accidentally write.
AGENT_READ_TOOLS = [t for t in AGENT_TOOLS if t["name"] in {"read_file", "list_dir", "find_files", "grep_files", "git"}]


def _scaffold_context(work_dir: str, task: str, context: dict[str, Any], max_files: int = 8) -> str:
    """Pre-read the repo structure and most-relevant files.
    Returns a rich context string that we inject directly so the model just synthesises, not navigates.
    This is what Claude does: fill context with real data before asking the model to reason."""
    parts: list[str] = []

    # 1. Directory tree (top-level + one level deep)
    dir_result = _execute_tool("list_dir", {"directory": work_dir}, context)
    parts.append(f"=== Directory listing: {work_dir} ===\n{dir_result}")

    # 2. Recurse one level into subdirs that look like source dirs
    source_dirs: list[Path] = []
    try:
        top = Path(work_dir)
        for entry in sorted(top.iterdir(), key=lambda e: e.name):
            if entry.is_dir() and not entry.name.startswith(".") and entry.name not in {
                "node_modules", "__pycache__", ".git", "dist", "build", ".venv", "venv",
            }:
                source_dirs.append(entry)
    except Exception:
        pass

    for sd in source_dirs[:4]:
        sub = _execute_tool("list_dir", {"directory": str(sd)}, context)
        parts.append(f"\n=== {sd.name}/ ===\n{sub}")

    # 3. Identify relevant files based on task keywords
    task_words = {w.lower() for w in task.split() if len(w) > 3} - _REPO_NAME_STOP_WORDS
    candidates: list[tuple[int, Path]] = []
    try:
        for root_path in [Path(work_dir)] + source_dirs[:4]:
            for entry in root_path.iterdir():
                if not entry.is_file():
                    continue
                if entry.suffix not in {".py", ".ts", ".tsx", ".js", ".go", ".rs", ".java", ".md", ".yaml", ".yml", ".toml", ".json"}:
                    continue
                name_lower = entry.name.lower()
                score = sum(1 for w in task_words if w in name_lower)
                if entry.suffix in {".py", ".ts", ".tsx", ".go", ".rs"}:
                    score += 1
                if entry.name.lower() in {"readme.md", "main.py", "app.py", "index.ts", "main.ts", "cli.py"}:
                    score += 2
                candidates.append((score, entry))
    except Exception:
        pass

    candidates.sort(key=lambda x: (-x[0], x[1].name))

    # 4. Read top N files (cap each at 3000 chars to stay within context)
    read_count = 0
    for _, fpath in candidates:
        if read_count >= max_files:
            break
        content = _execute_tool("read_file", {"path": str(fpath)}, context)
        if content.startswith("Error"):
            continue
        parts.append(f"\n=== {fpath} ===\n{content[:3000]}")
        read_count += 1

    return "\n".join(parts)


def _execute_tool(name: str, arguments: dict[str, Any], context: dict[str, Any]) -> str:
    root = Path(context.get("repo_root") or context["cwd"])
    try:
        if name == "read_file":
            raw_path = arguments.get("path") or arguments.get("file_path") or ""
            p = Path(raw_path).expanduser()
            if not p.is_absolute():
                p = root / p
            return p.read_text(errors="replace")[:24000]

        if name == "write_file":
            raw_path = arguments.get("path") or arguments.get("file_path") or ""
            p = Path(raw_path).expanduser()
            if not p.is_absolute():
                p = root / p
            # Back up the original before overwriting so /undo works
            if p.exists():
                _record_undo(str(p), p.read_bytes())
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(arguments["content"])
            return f"Wrote {len(arguments['content'])} chars to {p}"

        if name == "bash":
            command = arguments["command"]
            cwd = arguments.get("cwd") or str(root)
            # Block outright dangerous commands — don't even ask, just refuse
            if _is_dangerous_bash(command):
                return (
                    f"Error: refused dangerous command: {command!r}. "
                    "Use a safer alternative or confirm with the user first."
                )
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            out = (result.stdout + result.stderr).strip()
            return out[:8000] if out else "(no output)"

        if name == "list_dir":
            raw_path = arguments.get("directory") or arguments.get("path") or ""
            p = Path(raw_path).expanduser()
            if not p.is_absolute():
                p = root / p
            items = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
            return "\n".join(
                ("  " if e.is_file() else "/ ") + e.name for e in items[:200]
            )

        if name == "find_files":
            import glob as _glob
            search_root = Path(arguments.get("root") or str(root))
            pattern = arguments["pattern"]
            matches = _glob.glob(
                str(search_root / "**" / pattern.lstrip("/")), recursive=True
            )
            return "\n".join(matches[:100]) or "(no matches)"

        if name == "grep_files":
            import subprocess as _sp
            search_root = str(Path(arguments.get("root") or str(root)))
            pattern = arguments.get("pattern") or arguments.get("query") or ""
            file_glob = arguments.get("glob") or "*"
            result = _sp.run(
                ["grep", "-rn", "--include", file_glob, "-m", "5", "--", pattern, search_root],
                capture_output=True, text=True, timeout=30,
            )
            output = result.stdout.strip()
            if not output:
                return f"No matches for {pattern!r} in {search_root}"
            # Cap at 200 lines to avoid flooding context
            lines = output.splitlines()[:200]
            return "\n".join(lines)

        if name == "git":
            subcommand = arguments.get("command") or arguments.get("subcommand") or ""
            safe_cmds = {"log", "diff", "status", "show", "branch", "blame", "shortlog"}
            first_word = subcommand.strip().split()[0] if subcommand.strip() else ""
            if first_word not in safe_cmds:
                return f"Error: only read-only git commands allowed ({', '.join(sorted(safe_cmds))})"
            result = subprocess.run(
                f"git {subcommand}",
                shell=True,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            out = (result.stdout + result.stderr).strip()
            return out[:8000] if out else "(no output)"

        return f"Unknown tool: {name}"
    except Exception as exc:
        return f"Error running {name}: {exc}"


_REFUSAL_PHRASES = [
    "i'm sorry",
    "i cannot",
    "i can't assist",
    "i apologize",
    '"response": "i',
    "not able to",
    "unable to assist",
]


def _is_refusal(content: str) -> bool:
    lowered = content.lower()
    return any(phrase in lowered for phrase in _REFUSAL_PHRASES)


_WRITE_VERBS = {
    "add", "create", "write", "implement", "build", "fix", "refactor",
    "delete", "remove", "rename", "move", "update", "edit", "change",
    "install", "run", "execute", "test", "generate", "scaffold",
}

_READ_VERBS = {
    "check", "look", "analyze", "analyse", "review", "examine", "inspect",
    "summarize", "summarise", "audit", "find", "search", "list", "show",
    "describe", "explain", "compare", "identify", "assess",
}

# Conversational patterns that must never be routed to the agent
_CONVERSATIONAL_PATTERNS = [
    r"^how are (you|u)(\s+doing)?\??$",
    r"^how can (you|u|i)\b",                        # "how can you help", "how can i use you"
    r"^what can (you|u) (do|help)\b",               # "what can you do", "what can u help with"
    r"^(can you|could you) (help|tell|explain)\b",   # "can you help me"
    r"^(hey|hi|hello|sup|yo|hiya|howdy)[\s!?.]*$",
    r"^(good\s+)?(morning|afternoon|evening|night)[\s!?.]*$",
    r"^what('s| is) up\??$",
    r"^(thanks?|thank you|cheers|ty)[\s!.]*$",
    r"^(ok|okay|cool|got it|sounds good|nice|great|perfect|awesome)[\s!.]*$",
    r"^(yes|no|yep|nope|yeah|nah|sure|alright)[\s!.]*$",
    r"^(bye|goodbye|see ya|later|cya)[\s!.]*$",
    r"^(lol|haha|hehe|😂|👍|🙏)[\s!.]*$",
    r"^(who are you|what are you|introduce yourself)\??$",
    r"^help(\s+me)?\??$",
]


def _is_conversational(prompt: str) -> bool:
    """True for greetings, small talk, and one-word acks that must not go to agent_loop."""
    import re
    p = prompt.strip().lower()
    if len(p.split()) <= 1 and p not in _WRITE_VERBS and p not in _READ_VERBS:
        return True
    return any(re.search(pat, p) for pat in _CONVERSATIONAL_PATTERNS)


# ── Model auto-selection ───────────────────────────────────────────────────────

# Ordered preference lists per task mode.  First match that is actually
# installed in Ollama wins; falls back to whatever the user has set.
_MODEL_PREF: dict[str, list[str]] = {
    "chat": [
        "llama3.2:3b", "llama3.2:1b", "gemma3:1b", "phi3.5:3.8b", "gemma2:2b",
        "gemma3:4b", "llama3.2:11b", "mistral:latest", "mistral:7b", "mistral",
        "qwen2.5:7b", "llama3.1:8b", "qwen2.5-coder:7b",
    ],
    "read": [
        "qwen2.5:72b", "llama3.3:70b", "llama3.1:70b", "gemma3:27b",
        "qwen2.5:32b", "qwen2.5:14b", "phi4:14b", "gemma3:12b", "gemma2:27b",
        "mistral:latest", "mistral:7b", "mistral",
        "qwen2.5:7b", "llama3.1:8b", "qwen2.5-coder:7b",
    ],
    "write": [
        "qwen2.5-coder:32b", "codellama:70b", "codellama:34b",
        "deepseek-r1:32b", "deepseek-r1:14b", "llama3.3:70b", "llama3.1:70b",
        "qwen2.5-coder:7b", "qwen2.5:32b", "qwen2.5:14b",
        "mistral:latest", "mistral:7b", "mistral", "llama3.1:8b",
    ],
}

_ollama_model_cache: tuple[float, set[str]] | None = None


def _available_ollama_models() -> set[str]:
    """Return model tags currently installed in Ollama, with a 60-second cache."""
    global _ollama_model_cache
    import time
    now = time.monotonic()
    if _ollama_model_cache and now - _ollama_model_cache[0] < 60:
        return _ollama_model_cache[1]
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
        models = {m["name"] for m in data.get("models", [])}
    except Exception:
        models = set()
    _ollama_model_cache = (now, models)
    return models


def _resolve_model_in_available(model_name: str, available: set[str]) -> str | None:
    """Return the installed tag for model_name, or None if not found."""
    if model_name in available:
        return model_name
    if model_name + ":latest" in available:
        return model_name + ":latest"
    prefix = model_name + ":"
    matches = sorted(m for m in available if m.startswith(prefix))
    return matches[0] if matches else None


def _pick_model(mode: str, default_model: str) -> tuple[str, bool]:
    """Return (model_name, was_auto_selected).
    Honors the user's model if it is installed; only auto-selects when the
    requested model is not available in Ollama."""
    available = _available_ollama_models()
    if not available:
        return default_model, False
    resolved = _resolve_model_in_available(default_model, available)
    if resolved is not None:
        return resolved, resolved != default_model
    for candidate in _MODEL_PREF.get(mode, _MODEL_PREF["read"]):
        if candidate in available:
            return candidate, True
    return default_model, False


def _is_foreign_repo(prompt: str, context: dict[str, Any]) -> bool:
    """True when the prompt names a specific project that isn't the current working repo."""
    name = _foreign_repo_name(prompt)
    if not name:
        return False
    current = Path(context.get("repo_root") or context["cwd"]).name.lower()
    return name.lower() != current


_REPO_NAME_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "this", "that", "my", "our", "your", "its", "me", "you", "we",
    "repo", "repository", "codebase", "project", "code", "source",
    "tell", "show", "find", "look", "what", "how", "why", "where", "who",
    "bugs", "bug", "issues", "issue", "errors", "error", "features", "feature",
    "missing", "existing", "current", "all", "any", "some", "more",
    "please", "just", "really", "actually", "also", "then", "now",
}


def _foreign_repo_name(prompt: str) -> str:
    """Extract a project/repo name from the prompt, or empty string if none found."""
    import re

    def _valid(name: str) -> str:
        # Must be at least 4 chars and not a stop word
        if len(name) < 3:
            return ""
        return name if name.lower() not in _REPO_NAME_STOP_WORDS else ""

    # "growthos repo", "growthos codebase" — word BEFORE the keyword
    for m in re.finditer(
        r"\b([A-Za-z][\w-]+)\s+(?:repo|repository|codebase|project)\b",
        prompt, re.IGNORECASE,
    ):
        result = _valid(m.group(1))
        if result:
            return result

    # "repo growthos", "the repository growthos" — word AFTER the keyword
    for m in re.finditer(
        r"\b(?:repo|repository|codebase|project)\s+([A-Za-z][\w-]+)\b",
        prompt, re.IGNORECASE,
    ):
        result = _valid(m.group(1))
        if result:
            return result

    # "bugs in growthos", "missing in growthos", "issues in growthos"
    for m in re.finditer(
        r"\b(?:bugs?|issues?|errors?|features?|problems?|missing)\s+in\s+([A-Za-z][\w-]+)\b",
        prompt, re.IGNORECASE,
    ):
        result = _valid(m.group(1))
        if result:
            return result

    # "review/check/examine growthos" — verb directly followed by name (no "the repo" in between)
    for m in re.finditer(
        r"\b(?:review|check|analyze|analyse|examine|inspect|audit)\s+(?:the\s+)?([A-Za-z][\w-]{2,})\b",
        prompt, re.IGNORECASE,
    ):
        result = _valid(m.group(1))
        if result:
            return result

    return ""


def _extract_path_from_prompt(prompt: str) -> str | None:
    """Return the first existing path found in the prompt.
    Handles backslashes, absolute paths, and home-relative paths."""
    import re
    for match in re.finditer(r"([~/][^\s,;\"']+)", prompt):
        raw = match.group(1).replace("\\", "/")
        for candidate in [
            Path(raw).expanduser(),
            Path.home() / raw.lstrip("/"),
        ]:
            try:
                if candidate.exists():
                    return str(candidate.resolve())
            except (OSError, ValueError):
                continue
    return None


def _resolve_path_reply(raw: str) -> str | None:
    """Try to resolve a bare path string typed by the user (handles backslashes, ~ etc)."""
    raw = raw.strip().replace("\\", "/")
    for candidate in [
        Path(raw).expanduser(),
        Path.home() / raw.lstrip("/"),
    ]:
        try:
            if candidate.exists():
                return str(candidate.resolve())
        except (OSError, ValueError):
            continue
    return None


def _prompt_mode(prompt: str) -> str:
    """Return 'write', 'read', or 'chat' based on prompt intent."""
    # Greetings and small talk must always stay in chat — check first.
    if _is_conversational(prompt):
        return "chat"
    words = prompt.strip().lower().split()
    first = words[0] if words else ""
    if first in _WRITE_VERBS:
        return "write"
    if first in _READ_VERBS:
        return "read"
    # "what are the bugs in growthos" — "what" alone doesn't trigger read
    # but if it references a repo + analysis context, treat as read
    if first in {"what", "tell", "how"} and any(v in words for v in _READ_VERBS):
        return "read"
    if first in {"what", "tell", "how"} and _foreign_repo_name(prompt):
        return "read"
    # Fallback: write/read keywords anywhere in short prompts
    if any(v in words for v in _WRITE_VERBS):
        return "write"
    if any(v in words for v in _READ_VERBS):
        return "read"
    # Path provided → user is directing the agent to a specific location
    if _extract_path_from_prompt(prompt):
        return "read"
    return "chat"


_AGENTIC_CONTENT_MARKERS = [
    "=== Directory listing:",
    "=== Directory:",
    "TASK:",
    "TARGET DIRECTORY:",
    "FIRST TOOL CALL:",
    "I have pre-read the repository",
    "Auto-executed list_dir",
    "[Auto-executed",
]


def _is_agentic_message(content: str) -> bool:
    """True if this message contains scaffolded tool output that would confuse a chat model."""
    if not isinstance(content, str):
        return True  # tool result objects, image blocks — skip these too
    return any(marker in content for marker in _AGENTIC_CONTENT_MARKERS)


def _clean_chat_history(history: list[dict]) -> list[dict]:
    """Strip agentic scaffolding from session history so chat model isn't confused."""
    clean = []
    for msg in history:
        content = msg.get("content", "")
        if _is_agentic_message(str(content)):
            continue
        if msg.get("role") == "tool":
            continue
        clean.append({"role": msg["role"], "content": content})
    return clean


def _build_chat_payload(prompt: str, model: str, context: dict[str, Any], *, conversational: bool = False) -> dict[str, Any]:
    if conversational:
        # Greetings / small talk: zero history, minimal system prompt.
        messages = [{"role": "user", "content": prompt}]
        system = (
            "You are Xyntra, a helpful AI coding assistant. "
            "Always respond in bullet points — never paragraphs. "
            "Each bullet must be a complete, specific statement."
        )
    else:
        history = get_json(
            f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages"
        )
        # Strip agentic scaffolding and cap at last 6 exchanges (12 messages)
        # to prevent stale tool-call context from poisoning chat answers.
        clean = _clean_chat_history(history)
        messages = clean[-12:]
        messages.append({"role": "user", "content": prompt})
        # Use a plain chat prompt here — NOT the agentic tool-call system prompt.
        # Sending tool call format examples to a chat endpoint causes small models
        # to output raw JSON instead of answering the question.
        work_dir = context.get("repo_root") or context["cwd"]
        system = (
            "You are Xyntra, a helpful AI coding assistant. "
            "Answer in bullet points only — never paragraphs, never JSON, never tool call syntax. "
            "Be specific and concrete. No generic advice. "
            f"Working directory: {work_dir}"
        )
    return {
        "model": model,
        "local_only": context.get("local_only", True),
        "stream": True,
        "system_prompt": system,
        "messages": messages,
        "metadata": {
            "project_id": context["project_id"],
            "session_id": context["session_id"],
        },
    }


def _extract_write_calls(content: str, work_dir: str) -> list[dict[str, Any]]:
    """Parse code blocks the model printed as text and convert to write_file calls."""
    import re
    # Match ```lang\n# /some/path.py\n<code>``` or just ```lang\n<code>```
    pattern = r"```[^\n]*\n(?:#\s*([^\n]+)\n)?(.*?)```"
    calls = []
    for file_hint, code in re.findall(pattern, content, re.DOTALL):
        code = code.strip()
        if not code:
            continue
        file_hint = file_hint.strip()
        # Accept hint only if it looks like a real absolute path
        if file_hint and (file_hint.startswith("/") or file_hint.startswith("~")):
            path = file_hint
        else:
            continue  # can't infer path safely
        calls.append({"name": "write_file", "arguments": {"file_path": path, "content": code}})
    return calls


def _run_agent(
    *,
    prompt: str,
    mode: str,
    current_model: str,
    context: dict[str, Any],
    override_work_dir: str | None,
) -> str:
    """Run agent_loop and return the final response text.
    If the response is generic (no tools used), auto-retry once with a harsher prompt."""
    result: list[str] = []

    def _loop(p: str) -> None:
        agent_loop(
            prompt=p,
            model=current_model,
            context=context,
            read_only=(mode == "read"),
            override_work_dir=override_work_dir,
            _capture=result,
        )

    _loop(prompt)
    content = result[0] if result else ""

    if _is_generic_response(content):
        print(style(
            "\n  ↻ Response was generic — retrying with stricter tool enforcement…",
            "warn",
        ))
        save_feedback(
            "I gave generic advice instead of reading actual files. "
            "PROHIBITED: bullet lists of suggestions. REQUIRED: call list_dir then read_file first."
        )
        # Identify which signals caused the rejection so the model knows exactly what to fix
        lower_content = content.lower()
        triggered = [s for s in _GENERIC_SIGNALS if s in lower_content]
        retry_prompt = (
            f"REJECTED. Your response contained these banned phrases: {triggered}\n\n"
            f"TASK: {prompt}\n\n"
            f"RULES:\n"
            f"- Respond in bullet points ONLY. No paragraphs.\n"
            f"- Each bullet: '- <specific finding> (<file>:<function or line>)'\n"
            f"- Name specific files, functions, or lines for every claim.\n"
            f"- 'This codebase has X' not 'You could add X'.\n"
            f"- Never say 'you can call', 'I suggest', 'it's impossible', 'you should', 'without running'.\n"
            f"- If you need more data, call read_file on the specific path — don't hedge.\n"
            f"Answer directly in bullets."
        )
        result.clear()
        _loop(retry_prompt)
        content = result[0] if result else content

    return content


def agent_loop(
    *,
    prompt: str,
    model: str,
    context: dict[str, Any],
    max_steps: int = 30,
    read_only: bool = False,
    override_work_dir: str | None = None,
    _capture: list[str] | None = None,
) -> None:
    """_capture: if provided, final response text is appended to it (used by _run_agent for self-review)."""
    history = get_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages"
    )
    messages: list[dict[str, Any]] = [
        {"role": m["role"], "content": m["content"]} for m in history
    ]
    # Prefer explicit override (from routing), then path in prompt, then project root.
    mentioned_path = override_work_dir or _extract_path_from_prompt(prompt)
    work_dir = mentioned_path or context.get("repo_root") or context["cwd"]

    tools = AGENT_READ_TOOLS if read_only else AGENT_TOOLS
    system_prompt = build_system_prompt(context)

    if read_only:
        # ── Scaffolded read: pre-execute file discovery ourselves ─────────────
        # Claude's lesson: fill the model's context with real data instead of
        # asking a weak model to navigate. The model just needs to reason.
        # Broad questions (features, architecture, market) need more files than bug checks
        _broad_keywords = {"feature", "features", "market", "leading", "missing", "architecture", "improve", "roadmap", "product", "compare"}
        _prompt_words = set(prompt.lower().split())
        max_files = 16 if _broad_keywords & _prompt_words else 8
        print(style(f"  ◎ Scanning {work_dir}…", "muted"), end="\r", flush=True)
        scaffolded = _scaffold_context(work_dir, prompt, context, max_files=max_files)
        print(" " * 60, end="\r", flush=True)  # clear the scanning line
        tool_trigger = (
            f"TASK: {prompt}\n\n"
            f"The repository at {work_dir} has been pre-read. "
            f"Actual directory structure and file contents are below.\n\n"
            f"{scaffolded}\n\n"
            f"ANSWER RULES — violating any rule causes the answer to be rejected and retried:\n"
            f"1. Answer ONLY from the file contents above. No outside knowledge.\n"
            f"2. FORMAT: respond in bullet points only. No paragraphs, no prose.\n"
            f"   Each bullet: '- <finding> (<file> or <file>:<function>)'\n"
            f"3. Every claim must name the specific file it comes from.\n"
            f"4. PROHIBITED phrases: 'you should', 'you could', 'I suggest', 'it's impossible',\n"
            f"   'without running', 'you can call', 'consider', 'it would be worth', 'to get a better'.\n"
            f"5. DO NOT suggest the user run commands or check files — you already have the data.\n"
            f"6. If asked about bugs: one bullet per bug — file, function, exact issue.\n"
            f"7. If asked about missing features: one bullet per feature — what exists vs what's absent.\n"
            f"8. If asked about market improvements: one bullet per gap found in actual code.\n"
            f"9. If file contents are insufficient, call read_file on the exact path — don't hedge.\n"
        )
    else:
        tool_trigger = (
            f"TASK: {prompt}\n\n"
            f"TARGET DIRECTORY: {work_dir}\n"
            f"Call list_dir(\"{work_dir}\") first, then read_file on relevant files, "
            f"then write_file to make changes.\n"
            f"Output tool calls as JSON: {{\"name\": \"tool_name\", \"arguments\": {{...}}}}\n"
            f"Do NOT use markdown code blocks. Do NOT explain — act immediately."
        )
    messages.append({"role": "user", "content": tool_trigger})

    save_session_message(context, role="user", content=prompt, attachments=[])

    for step in range(max_steps):
        payload: dict[str, Any] = {
            "model": model,
            "local_only": context.get("local_only", True),
            "stream": False,
            "system_prompt": system_prompt,
            "tool_definitions": tools,
            "messages": messages,
            "metadata": {
                "project_id": context["project_id"],
                "session_id": context["session_id"],
                "cwd": context["cwd"],
                "repo_root": context.get("repo_root"),
                "tool_choice": "required" if not read_only and step == 0 else None,
            },
        }
        spin_label = f"Thinking… (step {step + 1})"
        stop_spin = _spin(spin_label)
        try:
            response = post_json("/chat", payload)
        except Exception as exc:
            stop_spin()
            print(style(f"  ✗ API error: {exc}", "err"))
            return
        finally:
            stop_spin()

        resp = response.get("response", {})
        content: str = resp.get("content") or ""
        tool_calls: list[dict[str, Any]] = resp.get("tool_calls") or []

        recovered = False
        if not tool_calls:
            # In read-only mode on the very first step: the model must read files
            # before giving an answer. If it skipped tools, force it.
            if read_only and step == 0 and content and not _is_refusal(content):
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": (
                        f"You have not read any files yet. "
                        f"Call list_dir(directory=\"{work_dir}\") right now, "
                        "then read_file on the key files before answering."
                    ),
                })
                continue

            # Detect model refusals — accumulated stale context confuses small models.
            if _is_refusal(content):
                print(style(
                    "\n  ✗ Model refused the task (context may be stale).\n"
                    "  Run /reset to clear history and try again.",
                    "warn",
                ))
                return

            recovered_calls = _extract_write_calls(content, work_dir)
            if recovered_calls:
                # Model wrote code as text — execute the writes directly and stop.
                recovered = True
                tool_calls = recovered_calls
            else:
                # Genuine final answer — stream-print it line by line.
                if content:
                    print()
                    for line in content.splitlines():
                        print(line)
                        time.sleep(0.004)
                    print()
                if _capture is not None:
                    _capture.append(content)
                save_session_message(context, role="assistant", content=content, attachments=[])
                state = load_state()
                key = current_context_key()
                if key in state.get("contexts", {}):
                    state["contexts"][key]["last_model"] = model
                    save_state(state)
                return

        # Show non-markdown content as a thought bubble before the tool calls.
        if content and not recovered:
            stripped = content.strip()
            if not stripped.startswith("```"):
                print(f"\n{style('◆', 'purple')} {stripped}")
        if not recovered:
            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})

        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("arguments") or {}
            arg_str = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
            print(f"  {style('▶', 'cyan')} {style(name, 'bold')}({style(arg_str, 'muted')})")
            exec_stop = _spin(f"  running {name}…")
            try:
                result = _execute_tool(name, args, context)
            finally:
                exec_stop()
            ok = not result.startswith("Error")
            icon = style("✓", "ok") if ok else style("✗", "err")
            preview = result[:160].replace("\n", " ")
            print(f"  {icon} {style(preview, 'muted')}")
            if not recovered:
                messages.append({"role": "tool", "content": result, "name": name})

        if recovered:
            # Done — don't loop back and ask the model again.
            save_session_message(context, role="assistant", content=content, attachments=[])
            return

    print(style("\n◆ Reached max steps.", "warn"))


def build_system_prompt(context: dict[str, Any]) -> str:
    repo = detect_repo()
    file_context = build_file_context(repo)
    parts = [
        "You are Xyntra, an autonomous coding agent with tools to read files, write files, and run shell commands.",
        "",
        "MANDATORY TOOL USE RULES — follow every single one:",
        "1. ALWAYS use tools. Never describe what you would do — just do it.",
        "2. To understand a codebase, call list_dir and find_files first, then read_file on relevant files.",
        "3. To create or change code, call write_file with the complete new file content.",
        "4. To run tests, install packages, or check git status, call bash.",
        "5. Never say 'I cannot', 'I suggest', 'a developer should', or 'you need to'.",
        "6. When calling tools: do it immediately — no preamble, no explanation before the call.",
        "7. If you are unsure what files exist, call list_dir — do not ask the user.",
        "8. Complete tasks end-to-end: explore → read → write → verify with bash.",
        "9. PROHIBITED: generic advice, paragraph prose, step-by-step guides for the user.",
        "10. When asked to identify/point out something: list the SPECIFIC items found in actual files.",
        "11. When asked about bugs/missing features: name the actual file, the actual line, the actual issue.",
        "",
        "OUTPUT FORMAT — MANDATORY FOR ALL TEXT RESPONSES:",
        "- Always answer in bullet points. Every answer, every response, every observation.",
        "- Never write paragraphs. If it takes more than one sentence, use sub-bullets.",
        "- Each bullet must be a complete, specific statement — no vague filler.",
        "- Format: '- <specific finding> (<file>:<line or function>)'",
        "",
        "TOOL CALL FORMAT — output ONLY raw JSON, never in a markdown code block:",
        '  {"name": "list_dir", "arguments": {"directory": "/path"}}',
        '  {"name": "read_file", "arguments": {"path": "/path/file.py"}}',
        '  {"name": "write_file", "arguments": {"file_path": "/path/file.py", "content": "..."}}',
        '  {"name": "bash", "arguments": {"command": "cd /path && python -m pytest"}}',
        "Do NOT wrap tool calls in ```python``` or any other fence. Do NOT say 'please run'.",
        "",
        "CONTEXT:",
        f"cwd: {repo['cwd']}",
        f"repo_root: {repo.get('repo_root')}",
        f"branch: {repo.get('branch')}",
        f"changed_files: {repo.get('changed_files')}",
    ]
    feedbacks = load_feedback()
    if feedbacks:
        parts.append("")
        parts.append("LEARNED FROM PAST MISTAKES (never repeat these):")
        for lesson in feedbacks[-5:]:
            parts.append(f"- {lesson}")
    if file_context["files"]:
        parts.append("\nRecent changed files:")
        for item in file_context["files"]:
            parts.append(f"\n[path] {item['path']}\n{item['content']}")
    return "\n".join(parts)


def _build_user_content(
    prompt: str, attachments: list[dict[str, Any]]
) -> str | list[dict[str, Any]]:
    text_parts: list[str] = []
    image_blocks: list[dict[str, Any]] = []
    for att in attachments:
        if att["type"] == "text_file":
            text_parts.append(
                f"[Attached file: {att['path']}]\n```\n{att['content']}\n```"
            )
        elif att["type"] == "image":
            image_blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": att["media_type"],
                        "data": att["data"],
                    },
                }
            )
    if not text_parts and not image_blocks:
        return prompt
    full_text = "\n\n".join(text_parts + [prompt]) if text_parts else prompt
    if not image_blocks:
        return full_text
    return image_blocks + [{"type": "text", "text": full_text}]


def chat_once(
    *,
    prompt: str,
    model: str,
    context: dict[str, Any],
    stream: bool,
    attachments: list[dict[str, Any]] | None = None,
) -> str:
    attachments = attachments or []
    system_prompt = build_system_prompt(context)
    messages = get_json(
        f"/projects/{context['project_id']}/sessions/{context['session_id']}/messages"
    )
    user_content = _build_user_content(prompt, attachments)
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
        + [{"role": "user", "content": user_content}],
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
    stop_spin = _spin("Thinking…")
    try:
        resp_ctx = urllib.request.urlopen(request, timeout=180)
    except urllib.error.HTTPError as exc:
        stop_spin()
        body = exc.read().decode("utf-8", errors="replace")
        print(
            style(f"  ✗ API error {exc.code}: {body[:300]}", "err") + "\n"
            + style("  Tip: if the session is too large, run /reset to start fresh.", "muted")
        )
        return ""
    except urllib.error.URLError as exc:
        stop_spin()
        print(style(f"  ✗ Connection error: {exc.reason}", "err"))
        return ""
    first_chunk = True
    with resp_ctx as response:
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
            data = json.loads(line.split(": ", 1)[1])
            if event_name == "chunk":
                delta = data.get("delta", "")
                if delta:
                    if first_chunk:
                        stop_spin()
                        print()
                        first_chunk = False
                    content_parts.append(delta)
                    print(delta, end="", flush=True)
    stop_spin()
    if first_chunk:
        print(
            style("  ✗ No response received.", "warn")
            + " The model may still be loading — try again in a moment."
        )
    else:
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

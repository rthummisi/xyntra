# xyntra

Version `1.0.0` includes a contract-validation workflow that can take a spec or coding contract, refine it through ChatGPT, then Kimi, then Claude, and emit a major-version contract package with a `WHATS_INCLUDED` companion file.

Local-machine AI execution control plane with a local backend and React control-plane UI.

## Status

Backend Phases 1-18 are implemented in-repo, and the Phase 19-24 frontend control plane now lives under `ui/`. The stack includes live pages for dashboard, chat, projects, sessions, tasks, providers, comparison, analytics, events, webhooks, evals, and operational contract views for backend capabilities that do not yet expose dedicated UI APIs.

## Local Startup

Run the single startup script:

```bash
./scripts/start_xyntra.sh
```

It handles the local prerequisites automatically:
- creates `.env` from `.env.example` if needed
- builds API and worker images
- starts PostgreSQL, Redis, Ollama, API, worker, and UI
- enables the `vector` extension
- creates the `xyntra_test` database if missing
- applies Alembic migrations
- waits for API and UI readiness

Optional seeded startup:

```bash
SEED_DEV_DATA=true ./scripts/start_xyntra.sh
```

Check service health:

```bash
curl http://localhost:${API_HOST_PORT:-18000}/api/v1/health
curl http://localhost:${API_HOST_PORT:-18000}/api/v1/ready
```

Open the control plane:

```bash
open http://localhost:${UI_HOST_PORT:-4173}
```

Manual seed command if you need it separately:

```bash
./scripts/seed_dev_data.sh
```

## CLI Invocation

Install the project once so the console commands are available from any working directory:

```bash
pip install -e /Users/raghunathvenkataramanathummisi/downloads/projects/xyntra
```

CLI commands:

```bash
xyntra
xyntra web
xyntra web try-xyntra
xyntra web pricing
xyntra web demo
xyntra validate-contract ./SPEC.md --major-version 1 --kimi-model <kimi-model>
xyntra run "Summarize this repo"
xyntra exec pwd
xyntra test
xyntra test pytest tests/unit
xyntra status
xyntra start
xyntra-api
```

CLI behavior:
- `xyntra` starts the stack if needed, then opens an interactive terminal session
- `xyntra web` opens the local public-site preview at `/`
- `/coding projects validation ./SPEC.md --major-version 1 --kimi-model <kimi-model>` is available in the interactive shell and is shown up front in the welcome flow
- `xyntra validate-contract ...` reads a spec or coding contract, runs a refinement chain through ChatGPT, Kimi, and Claude, then writes a major-version contract, `WHATS_INCLUDED` notes, and an audit JSON file
- `xyntra run "..."` sends a one-shot prompt while retaining directory-scoped context
- `xyntra exec ...` runs a terminal command in the current repo root when available, streams output, and stores the transcript in the active session
- `xyntra test` auto-detects a default test command (`pytest` for this repo) unless you pass an explicit command
- `xyntra status` shows service readiness and the current retained context
- `xyntra start` runs the full startup flow only
- `xyntra-api` runs only the FastAPI server

CLI context retention:
- context is retained per working directory
- the CLI stores `cwd -> project_id/session_id/user_id` in `~/.xyntra/cli_state.json`
- repeated calls from the same directory reuse that project/session
- command invocations and captured output are persisted into the active backend session
- request metadata includes `cwd`, hostname, and terminal type
- the CLI does not capture shell scrollback or arbitrary terminal process state

Repo-local shortcut:
- from the repo root, `xyntra/web` delegates to `xyntra web`

Default CLI model:
- interactive/default model: `llama3.2:3b`
- default routing mode: `local_only=true`
- embedding model: `nomic-embed-text`

Contract validation environment:
- `OPENAI_API_KEY` is required for the ChatGPT stage
- `KIMI_API_KEY` and either `KIMI_MODEL` or `--kimi-model` are required for the Kimi stage
- `ANTHROPIC_API_KEY` is required for the Claude stage
- optional overrides: `OPENAI_BASE_URL`, `KIMI_BASE_URL`, `ANTHROPIC_BASE_URL`

## Local Services

- FastAPI app on `http://localhost:${API_HOST_PORT:-18000}`
- React UI on `http://localhost:${UI_HOST_PORT:-4173}`
- PostgreSQL + pgvector on `localhost:${POSTGRES_HOST_PORT:-15432}`
- Redis on `localhost:${REDIS_HOST_PORT:-16379}`
- Ollama on `localhost:${OLLAMA_HOST_PORT:-21434}`

## Notes

- This project is local-machine only in V1.
- The frontend is a Vite/React TypeScript app under [`ui/`](./ui).
- If you prefer not to use Docker for the UI, run `cd ui && npm install && npm run dev`.
- `./scripts/dev_start.sh` and `./scripts/bootstrap_project.sh` now delegate to `./scripts/start_xyntra.sh`.

## API Examples

Health:

```bash
curl http://localhost:${API_HOST_PORT:-18000}/api/v1/health
```

Create project:

```bash
curl -X POST http://localhost:${API_HOST_PORT:-18000}/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "11111111-1111-1111-1111-111111111111",
    "name": "Example Project",
    "description": "Backend smoke test",
    "local_only": false,
    "token_quota": 50000
  }'
```

Create session:

```bash
curl -X POST http://localhost:${API_HOST_PORT:-18000}/api/v1/projects/<project_id>/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "11111111-1111-1111-1111-111111111111",
    "title": "Primary Session"
  }'
```

Unified chat:

```bash
curl -X POST http://localhost:${API_HOST_PORT:-18000}/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Summarize the system state."}],
    "local_only": false
  }'
```

OpenAI-compatible chat completions:

```bash
curl -X POST http://localhost:${API_HOST_PORT:-18000}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Hello from the OpenAI client shape"}]
  }'
```

Provider leaderboard:

```bash
curl http://localhost:${API_HOST_PORT:-18000}/api/v1/providers/leaderboard
```

Plan tasks:

```bash
curl -X POST http://localhost:${API_HOST_PORT:-18000}/api/v1/tasks/plan \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id>",
    "objective": "Bootstrap a routing test plan"
  }'
```

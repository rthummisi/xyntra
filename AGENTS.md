# Xyntra — Coding Contract

> This document is the authoritative contract for any coding agent building Xyntra.
> Read this before touching any code. Follow it exactly.

---

## What You Are Building

Xyntra is a **local-machine AI execution control plane** invoked as `xyntra`.

It is **not** a thin API proxy. It is **not** a chatbot wrapper.
It **is** a production-grade backend system that makes multiple AI models behave like one consistent, stateful, project-aware execution engine — running entirely on the local machine via `docker-compose`.

Full product definition, architecture, and 150-task build list are in [`SPEC.md`](./SPEC.md). Read it before starting any phase.

---

## Non-Negotiable Rules

### 1. Backend First
- V1 is backend-only (Phases 1–18, tasks 1–127).
- Frontend (Phases 19–24, tasks 128–150) begins only after V1 backend is stable and all backend success criteria pass.
- Do not scaffold UI code during backend phases.

### 2. Local Only
- All infrastructure runs via `docker-compose`. No cloud deployment in V1.
- Outbound calls go only to the 8 designated providers (Anthropic, OpenAI, Ollama, Gemini, Grok, Mistral, DeepSeek, Groq).
- `local_only` mode must send **zero bytes** to hosted providers — route to Ollama only.

### 3. Follow the Phase Order
- Build phases sequentially: 1 → 2 → 3 → … → 18.
- Do not skip ahead or start Phase N+1 until Phase N deliverables are complete.
- Each task has a specific file target in SPEC.md — deliver exactly those files.

### 4. One Task at a Time
- Complete one task fully before starting the next.
- Mark tasks done only when the file exists, tests pass (where applicable), and the feature works end-to-end.

---

## Tech Stack — Use Exactly This

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.12 | No other Python version |
| Framework | FastAPI | No Flask, Django, or alternatives |
| ORM | SQLAlchemy 2.x | Async style (`AsyncSession`) |
| Migrations | Alembic | Every schema change = a migration |
| Database | PostgreSQL + pgvector | pgvector required for semantic cache |
| Cache / Queue | Redis | Via `redis-py` async client |
| Workers | Celery or Dramatiq | Choose one, use it consistently |
| Validation | Pydantic v2 | All request/response schemas |
| Observability | OpenTelemetry + structured JSON logging | No `print()` statements in prod code |
| Testing | pytest | pytest-asyncio for async tests |
| Linting | ruff + black | Must pass before any commit |
| Containers | Docker + docker-compose | Local only |
| Auth | Bearer token / API key (V1) | RBAC abstraction ready but not implemented |

---

## File Structure

```
xyntra/
├── main.py                        # FastAPI app entry point
├── pyproject.toml                 # includes `xyntra` CLI entrypoint
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── .env.example                   # all 8 provider key slots
├── scripts/
│   ├── dev_start.sh
│   ├── seed_dev_data.sh
│   ├── bootstrap_project.sh
│   └── create_db.sh
├── alembic/
│   └── versions/
├── core/
│   ├── config.py                  # Pydantic settings
│   ├── database.py                # SQLAlchemy async engine
│   ├── redis.py
│   ├── logging.py
│   ├── rate_limiter.py
│   ├── security.py
│   ├── telemetry.py
│   ├── events.py
│   └── ollama_provisioner.py
├── models/                        # SQLAlchemy ORM models only
├── api/
│   └── v1/                        # All API routers
├── services/                      # Business logic
├── providers/                     # Adapter layer
│   ├── base/
│   └── [provider]_adapter.py
├── routing/                       # Router + strategies
├── context/                       # Context assembly engine
├── memory/                        # Memory layer
├── tasks/                         # Task graph + executor
├── verification/                  # Verification layer
├── artifacts/                     # Artifact storage
├── policies/                      # Privacy, cost, approval
├── workers/                       # Celery/Dramatiq workers
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

Frontend (Phase 19+):
```
ui/
├── src/
│   ├── pages/          # One file per surface (F-1 to F-23)
│   ├── components/
│   └── ...
```

---

## Code Standards

### Python
- All functions and methods must have type annotations.
- Use `async def` for all I/O-bound functions (DB, Redis, provider calls).
- No `print()` — use structured logging via `core/logging.py`.
- No bare `except:` — catch specific exceptions.
- Pydantic v2 for all request/response shapes — no raw dicts across service boundaries.
- Keep files under 400 lines. Split if larger.

### FastAPI
- All routers live in `api/v1/`.
- All routers registered in `main.py`.
- Every endpoint must have a Pydantic response model.
- Use `Depends()` for DB session injection.
- HTTP status codes: 200 (success), 201 (created), 400 (bad input), 404 (not found), 409 (conflict), 422 (validation), 500 (internal).

### SQLAlchemy
- Use `AsyncSession` exclusively — no sync sessions.
- All queries in service layer, never in routers.
- Every schema change requires an Alembic migration.
- Use `relationship()` with `lazy="selectin"` or explicit joins — no N+1 queries.

### Testing
- Unit tests: mock external I/O (providers, Redis), test logic in isolation.
- Integration tests: use a real test database (no mocks for DB).
- E2E tests: full HTTP request → response including DB state verification.
- Minimum coverage gate: 80% for services and routing layers.

### Comments
- Write no comments unless the WHY is non-obvious: a hidden constraint, a subtle invariant, a workaround for a specific bug.
- Do not explain WHAT the code does — well-named identifiers do that.

---

## Provider Adapters Contract

Each adapter must implement the base interface in `providers/base/adapter.py`:

```python
class BaseAdapter:
    async def complete(self, request: NormalizedRequest) -> NormalizedResponse: ...
    async def stream(self, request: NormalizedRequest) -> AsyncIterator[StreamChunk]: ...
    async def health_check(self) -> ProviderHealth: ...
    def normalize_request(self, unified: UnifiedRequest) -> ProviderRequest: ...
    def normalize_response(self, raw: Any) -> NormalizedResponse: ...
```

- All provider-specific formats are converted to/from the unified schema.
- Never leak provider-specific types outside the adapter module.
- Multi-modal inputs: images and PDFs routed only to capable models — check capability registry before routing.

---

## Routing Contract

The router must enforce in order:
1. **Policy check** (privacy, content, PII) — block before any model selection
2. **Capability filter** — only models that support the request type
3. **Strategy application** — cost / latency / quality / privacy
4. **Circuit breaker check** — skip unhealthy providers
5. **Latency SLA check** — enforce timeout thresholds
6. **Context window check** — auto-escalate if prompt overflows
7. **Fallback chain** — try next candidate on failure

Never return an error when a fallback is available.

---

## OpenAI Compatibility Contract

`/v1/chat/completions` must accept any OpenAI SDK client with zero code changes.

- Request shape: OpenAI `ChatCompletion` format
- Response shape: OpenAI `ChatCompletion` format
- Streaming: OpenAI SSE format (`data: {...}\n\n`, terminated by `data: [DONE]`)
- Model aliasing: map OpenAI model names to xyntra equivalents when needed
- Test: `tests/e2e/openai_compat/` must verify a real `openai` Python client works against xyntra

---

## Semantic Cache Contract

- Lookup uses pgvector cosine similarity on the prompt embedding.
- Similarity threshold: configurable, default `0.95`.
- Cache key includes: normalized prompt text + model family + system prompt hash.
- Cache miss: proceed to provider, store result with embedding.
- Cache hit: return stored response, log cache hit in `ProviderCall` record.
- Never return a cached response for `local_only` requests unless the cache entry was also generated via local model.

---

## Memory Contract

Four memory types, all queryable independently:

| Type | Scope | Key |
|------|-------|-----|
| Session | Per conversation | `session_id` |
| Project | Per project | `project_id` |
| Preference | Per user | `user_id` |
| Summary | Compacted session | `session_id` |

- Memory is assembled by the context engine, not injected directly into prompts.
- Compaction triggers when session token count exceeds the configured threshold.
- Project memory must survive across session resets.

---

## Privacy Contract

`local_only` mode is a hard guarantee — not a best-effort hint:

- If `local_only: true` is set on a project or request, the router must only consider Ollama adapters.
- Any attempt to route to a hosted provider must raise a `PrivacyViolation` error.
- PII detection runs **before** prompt assembly. Redact before embedding, before caching, before sending.
- PII redaction is logged but the original text is never stored unredacted in any DB table.

---

## Cost / Budget Contract

- Every provider call writes a `SpendRecord` with: provider, model, input tokens, output tokens, cost USD, project ID, session ID, task ID.
- Per-project token quota: if set, enforce hard cap — return `QuotaExceeded` error, do not route.
- Budget alert threshold: emit webhook event at 80% of quota consumed.
- Spend analytics API must support grouping by: project / session / model / date range.

---

## Dead Letter Queue Contract

- Any failed task that exhausts its retry budget lands in the DLQ — never silently dropped.
- DLQ entries must be inspectable via API: list, view payload, view error history, retry, or discard.
- Retry from DLQ requeues with the original task payload and a new `task_run_id`.

---

## Artifact Contract

- Artifacts are stored on local filesystem under a configurable root (default: `./artifacts/`).
- Every save creates a new version — never overwrite in place.
- Diff manager: compute and store text diffs between consecutive versions.
- Export formats: JSON (full metadata), Markdown (human-readable), ZIP (all versions).

---

## Webhook / Event Bus Contract

Events emitted by xyntra:

| Event | Trigger |
|-------|---------|
| `task.completed` | Task finishes successfully |
| `task.failed` | Task lands in DLQ |
| `approval.required` | Approval-gated execution paused |
| `budget.threshold` | Project at 80% quota |
| `budget.exceeded` | Project quota hard limit hit |
| `provider.circuit_open` | Circuit breaker trips on a provider |
| `session.branched` | Conversation fork created |
| `artifact.created` | New artifact version saved |

- Webhook delivery: HTTP POST with HMAC-SHA256 signature header.
- Retry: exponential backoff, max 5 attempts, then mark failed.
- Event log: all emitted events stored and queryable via API regardless of delivery status.

---

## What NOT to Build in V1

- No frontend UI (Phases 19–24 are V2)
- No multi-user collaboration
- No cloud deployment
- No repo graph ingestion
- No IDE plugin
- No advanced command execution sandboxes
- No benchmarking harness
- No authentication beyond API key / Bearer token

Do not add features outside the 127 backend tasks. Scope creep breaks the phase contract.

---

## Definition of Done (Per Task)

A task is done when:
1. The specified file(s) exist at the exact paths listed in SPEC.md
2. The code passes `ruff` and `black` with no errors
3. Relevant unit or integration tests exist and pass
4. The feature works end-to-end (not just unit-tested in isolation)
5. No regressions in previously completed tasks

---

## Commit Convention

```
<type>(<scope>): <short description>

Types: feat, fix, refactor, test, docs, chore
Scope: phase number or module (e.g. phase1, router, memory, providers)

Examples:
feat(phase1): bootstrap FastAPI app with health endpoints
feat(phase6): add circuit breaker with per-provider health state
test(phase16): add E2E test for OpenAI-compat layer
```

---

## How to Start

1. Read `SPEC.md` in full.
2. Read this document in full.
3. Start at **Phase 1, Task 1**: Bootstrap FastAPI app named `xyntra`.
4. Deliver `main.py` and `core/config.py`.
5. Proceed task by task.

Do not start Phase 2 until all 13 Phase 1 tasks are complete and verified.

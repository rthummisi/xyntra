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

## Full Task List (150 tasks — 127 backend + 23 frontend)

| # | Phase | Task | Key Deliverables |
|---|-------|------|-----------------|
| 1 | Phase 1 | Bootstrap FastAPI app named `xyntra` | `main.py`, `core/config.py` |
| 2 | Phase 1 | PostgreSQL + SQLAlchemy wiring | `core/database.py` |
| 3 | Phase 1 | Redis wiring (cache + queue) | `core/redis.py` |
| 4 | Phase 1 | Alembic setup + initial migration | `/alembic/`, `alembic.ini` |
| 5 | Phase 1 | Structured JSON logging + request IDs | `core/logging.py`, middleware |
| 6 | Phase 1 | Rate limiting middleware (per-API-key, per-project) | `core/rate_limiter.py` |
| 7 | Phase 1 | `/health` and `/ready` endpoints | `api/v1/health.py` |
| 8 | Phase 1 | Local-only Dockerfile + docker-compose | `Dockerfile`, `docker-compose.yml` |
| 9 | Phase 1 | Local Ollama auto-provisioner | `core/ollama_provisioner.py` |
| 10 | Phase 1 | `pyproject.toml` with `xyntra` CLI entrypoint | `pyproject.toml` |
| 11 | Phase 1 | `.env.example` with all 8 provider API key slots | `.env.example` |
| 12 | Phase 1 | `dev_start.sh` local launch script | `scripts/dev_start.sh` |
| 13 | Phase 1 | README startup instructions | `README.md` |
| 14 | Phase 2 | User model + migration | `models/user.py` |
| 15 | Phase 2 | Project + ProjectState models | `models/project.py`, `models/project_state.py` |
| 16 | Phase 2 | Session + Message models (with branch support) | `models/session.py`, `models/message.py` |
| 17 | Phase 2 | Task + TaskRun models | `models/task.py`, `models/task_run.py` |
| 18 | Phase 2 | Artifact model (versioned, local filesystem path) | `models/artifact.py` |
| 19 | Phase 2 | Decision model | `models/decision.py` |
| 20 | Phase 2 | ProviderCall model | `models/provider_call.py` |
| 21 | Phase 2 | MemorySummary + RetrievedContext models | `models/memory_summary.py`, `models/retrieved_context.py` |
| 22 | Phase 2 | Approval + PolicyRule models | `models/approval.py`, `models/policy_rule.py` |
| 23 | Phase 2 | PromptTemplate model (versioned, tagged, per-project) | `models/prompt_template.py` |
| 24 | Phase 2 | SemanticCache model | `models/semantic_cache.py` |
| 25 | Phase 2 | DeadLetterQueue model | `models/dead_letter.py` |
| 26 | Phase 2 | WebhookSubscription + WebhookEvent models | `models/webhook.py` |
| 27 | Phase 2 | SpendRecord model | `models/spend_record.py` |
| 28 | Phase 2 | ToolDefinition model | `models/tool_definition.py` |
| 29 | Phase 2 | Migrations applied, service-layer CRUD | Alembic migrations, service stubs |
| 30 | Phase 3 | Project CRUD API + service | `api/v1/projects.py`, `services/project_service.py` |
| 31 | Phase 3 | ProjectState structured schema + read/update | `services/project_state_service.py` |
| 32 | Phase 3 | Session CRUD under project | `api/v1/sessions.py`, `services/session_service.py` |
| 33 | Phase 3 | Message attachment to session | `services/session_service.py` |
| 34 | Phase 3 | Conversation branching — fork session at any message | `services/session_service.py` |
| 35 | Phase 4 | Raw message persistence + summarization | `memory/session_memory.py`, `memory/summary_memory.py` |
| 36 | Phase 4 | User preference memory | `memory/preference_memory.py` |
| 37 | Phase 4 | Project memory | `memory/project_memory.py` |
| 38 | Phase 4 | Memory snapshot (per session + per project) | `services/memory_service.py` |
| 39 | Phase 4 | Compaction + context rebuild hooks | `context/compactor.py` |
| 40 | Phase 5 | Base adapter interface | `providers/base/adapter.py` |
| 41 | Phase 5 | AnthropicAdapter | `providers/anthropic_adapter.py` |
| 42 | Phase 5 | OpenAIAdapter | `providers/openai_adapter.py` |
| 43 | Phase 5 | OllamaAdapter | `providers/ollama_adapter.py` |
| 44 | Phase 5 | GeminiAdapter | `providers/gemini_adapter.py` |
| 45 | Phase 5 | GrokAdapter | `providers/grok_adapter.py` |
| 46 | Phase 5 | MistralAdapter | `providers/mistral_adapter.py` |
| 47 | Phase 5 | DeepSeekAdapter | `providers/deepseek_adapter.py` |
| 48 | Phase 5 | GroqAdapter | `providers/groq_adapter.py` |
| 49 | Phase 5 | Multi-modal input normalization | `providers/base/multimodal.py` |
| 50 | Phase 5 | Unified tool/function registry | `providers/tool_registry.py` |
| 51 | Phase 5 | Provider registry + normalized response schema | `providers/registry.py` |
| 52 | Phase 6 | Capability registry — all ~94 models | `providers/capability_registry.py` |
| 53 | Phase 6 | Routing classifier | `routing/classifier.py` |
| 54 | Phase 6 | Routing strategies | `routing/strategies.py` |
| 55 | Phase 6 | Circuit breaker + health state | `routing/circuit_breaker.py`, `routing/health_state.py` |
| 56 | Phase 6 | Fallback logic | `routing/fallback.py` |
| 57 | Phase 6 | Budget enforcer | `routing/budgeter.py` |
| 58 | Phase 6 | Latency SLA enforcer | `routing/latency_sla.py` |
| 59 | Phase 6 | Context window auto-escalation | `routing/context_escalator.py` |
| 60 | Phase 6 | Routing service + router API endpoint | `services/routing_service.py`, `api/v1/router.py` |
| 61 | Phase 7 | Context selector + ranker + deduper | `context/selector.py` |
| 62 | Phase 7 | Token budget allocator | `context/token_budget.py` |
| 63 | Phase 7 | Semantic cache (Redis + pgvector) | `context/semantic_cache.py` |
| 64 | Phase 7 | Context assembler | `context/assembler.py` |
| 65 | Phase 7 | Project bootstrap context | `context/project_bootstrap.py` |
| 66 | Phase 7 | pgvector retrieval integration | `context/retrieval.py` |
| 67 | Phase 8 | Task planner | `tasks/planner.py` |
| 68 | Phase 8 | Task state machine | `tasks/state_machine.py` |
| 69 | Phase 8 | Task graph (dependency resolution) | `tasks/task_graph.py` |
| 70 | Phase 8 | Task executor | `tasks/executor.py` |
| 71 | Phase 8 | Async batch execution engine | `tasks/batch_executor.py` |
| 72 | Phase 8 | Dead letter queue handler | `workers/dlq_worker.py` |
| 73 | Phase 8 | Task API endpoints | `api/v1/tasks.py` |
| 74 | Phase 9 | Structured output validator | `verification/validators.py` |
| 75 | Phase 9 | Required-field + code patch validation | `verification/code_checks.py` |
| 76 | Phase 9 | Retry loop with validation feedback | `verification/retry_loop.py` |
| 77 | Phase 9 | Judge/eval model hook | `verification/judge.py` |
| 78 | Phase 9 | Approval-gated execution scaffold | `services/approval_service.py` |
| 79 | Phase 10 | Local filesystem artifact storage | `artifacts/storage.py` |
| 80 | Phase 10 | Artifact versioning + diff manager | `artifacts/versioning.py`, `artifacts/diff_manager.py` |
| 81 | Phase 10 | Artifact export (JSON, Markdown, ZIP) | `artifacts/exporter.py` |
| 82 | Phase 10 | Artifact API endpoints | `api/v1/artifacts.py` |
| 83 | Phase 11 | Decision record model + service | `services/decision_service.py` |
| 84 | Phase 11 | Project state updater | `services/project_state_service.py` |
| 85 | Phase 12 | PII detection + redaction pipeline | `policies/pii_detector.py` |
| 86 | Phase 12 | Prompt injection detector | `policies/injection_guard.py` |
| 87 | Phase 12 | Content policy guardrails | `policies/content_guard.py` |
| 88 | Phase 12 | Privacy-first routing (local_only mode) | `policies/privacy.py` |
| 89 | Phase 12 | Cost/budget policy + per-project token quota | `policies/cost.py` |
| 90 | Phase 12 | Approval policy + routing policy | `policies/approval.py`, `policies/routing_policy.py` |
| 91 | Phase 12 | API key rotation + expiry | `core/security.py` |
| 92 | Phase 12 | Policy service wired into router | `services/policy_service.py` |
| 93 | Phase 13 | OpenTelemetry tracing (local stdout/file) | `core/telemetry.py` |
| 94 | Phase 13 | ProviderCall full metadata storage | `models/provider_call.py` |
| 95 | Phase 13 | Spend analytics service + API | `services/cost_service.py`, `api/v1/analytics.py` |
| 96 | Phase 13 | Replay service + replay API | `services/replay_service.py`, `api/v1/replay.py` |
| 97 | Phase 14 | All endpoint wiring + router registration | `api/v1/chat.py`, `api/v1/providers.py` |
| 98 | Phase 14 | Unified chat/stream endpoint | `api/v1/chat.py` |
| 99 | Phase 14 | OpenAI-compatible drop-in layer | `api/v1/openai_compat.py` |
| 100 | Phase 14 | Provider health + capabilities endpoints | `api/v1/providers.py` |
| 101 | Phase 14 | Model leaderboard + price/quality matrix | `api/v1/providers.py` |
| 102 | Phase 14 | Output comparison endpoint | `api/v1/compare.py` |
| 103 | Phase 14 | Full OpenAPI/Swagger docs | FastAPI auto-docs |
| 104 | Phase 15 | Seed script | `scripts/seed_dev_data.sh` |
| 105 | Phase 15 | Bootstrap script | `scripts/bootstrap_project.sh` |
| 106 | Phase 15 | `create_db.sh` | `scripts/create_db.sh` |
| 107 | Phase 15 | curl examples for all key endpoints | `README.md` |
| 108 | Phase 15 | `xyntra` CLI entrypoint | `pyproject.toml` |
| 109 | Phase 16 | Unit tests: router, context, policies, cache, artifacts | `tests/unit/` |
| 110 | Phase 16 | Unit tests: all 8 provider adapter normalizations | `tests/unit/providers/` |
| 111 | Phase 16 | Unit tests: PII, injection guard, guardrails | `tests/unit/policies/` |
| 112 | Phase 16 | Unit tests: tool registry normalization | `tests/unit/tools/` |
| 113 | Phase 16 | Integration tests: DB, task lifecycle, DLQ, replay | `tests/integration/` |
| 114 | Phase 16 | Integration tests: Ollama local adapter | `tests/integration/providers/` |
| 115 | Phase 16 | Integration tests: semantic cache hit/miss | `tests/integration/cache/` |
| 116 | Phase 16 | E2E: full flow project → replay | `tests/e2e/` |
| 117 | Phase 16 | E2E: OpenAI-compat layer | `tests/e2e/openai_compat/` |
| 118 | Phase 17 | Prompt template registry CRUD API | `api/v1/prompts.py` |
| 119 | Phase 17 | Prompt template version diff + rollback | `services/prompt_service.py` |
| 120 | Phase 17 | Spend dashboard API | `api/v1/analytics.py` |
| 121 | Phase 17 | Per-project token quota enforcement + alerts | `services/cost_service.py` |
| 122 | Phase 17 | Eval harness | `services/eval_service.py`, `api/v1/evals.py` |
| 123 | Phase 17 | Output comparison mode | `api/v1/compare.py` |
| 124 | Phase 18 | Webhook subscription CRUD | `api/v1/webhooks.py` |
| 125 | Phase 18 | Event emitter | `core/events.py` |
| 126 | Phase 18 | Webhook delivery worker | `workers/webhook_worker.py` |
| 127 | Phase 18 | Event log API | `api/v1/events.py` |
| 128 | Phase 19 | Dashboard — system overview, provider health, spend summary, DLQ count | `ui/src/pages/Dashboard.tsx` |
| 129 | Phase 19 | Chat / Inference — message input, model selector, streaming view, branch button | `ui/src/pages/Chat.tsx` |
| 130 | Phase 19 | Projects — list/create, project state viewer, decisions timeline | `ui/src/pages/Projects.tsx` |
| 131 | Phase 19 | Sessions — list per project, threaded conversation view, branch fork UI | `ui/src/pages/Sessions.tsx` |
| 132 | Phase 19 | Tasks — task list, state machine badge, dependency graph, DLQ inspector | `ui/src/pages/Tasks.tsx` |
| 133 | Phase 20 | Model Leaderboard — ~94-model price/latency/quality matrix, sortable/filterable | `ui/src/pages/Leaderboard.tsx` |
| 134 | Phase 20 | Output Comparison — side-by-side N-model parallel response view | `ui/src/pages/Compare.tsx` |
| 135 | Phase 20 | Provider Health Panel — circuit breaker states, latency/error rates per provider | `ui/src/pages/ProviderHealth.tsx` |
| 136 | Phase 20 | Routing Decision Viewer — classifier output, strategy, fallback chain per request | `ui/src/pages/RoutingDecision.tsx` |
| 137 | Phase 21 | Memory Viewer — session, project, preference memory structured display | `ui/src/pages/Memory.tsx` |
| 138 | Phase 21 | Context Assembly Inspector — ranked chunks, token budget breakdown per request | `ui/src/pages/ContextInspector.tsx` |
| 139 | Phase 21 | Semantic Cache Browser — hit/miss log, similarity scores, cached entry viewer | `ui/src/pages/SemanticCache.tsx` |
| 140 | Phase 22 | Artifact Browser — versioned list, side-by-side diff, export JSON/MD/ZIP | `ui/src/pages/Artifacts.tsx` |
| 141 | Phase 22 | Prompt Template Registry — list/create/edit, version diff, rollback, tag filter | `ui/src/pages/PromptTemplates.tsx` |
| 142 | Phase 23 | Spend Analytics Dashboard — per-project/session/model cost charts, quota alerts | `ui/src/pages/SpendAnalytics.tsx` |
| 143 | Phase 23 | Trace / Replay Viewer — OTel span timeline, step-by-step replay | `ui/src/pages/Replay.tsx` |
| 144 | Phase 23 | Event Log — webhook event stream, filterable by type/project/provider | `ui/src/pages/EventLog.tsx` |
| 145 | Phase 24 | Policy Configuration — PII rules, guardrails, privacy routing, token quotas | `ui/src/pages/Policies.tsx` |
| 146 | Phase 24 | Approvals Queue — pending approvals, approve/reject with reason, audit trail | `ui/src/pages/Approvals.tsx` |
| 147 | Phase 24 | API Key Manager — create/rotate/expire keys, per-key usage, expiry warnings | `ui/src/pages/ApiKeys.tsx` |
| 148 | Phase 24 | Webhook Manager — subscription CRUD, delivery log, retry controls | `ui/src/pages/Webhooks.tsx` |
| 149 | Phase 24 | Eval Harness — run evals against prompt template, view scored comparison | `ui/src/pages/Evals.tsx` |
| 150 | Phase 24 | Settings — provider API keys, Ollama model pull UI, system defaults | `ui/src/pages/Settings.tsx` |

---

## How to Start

1. Read `SPEC.md` in full.
2. Read this document in full.
3. Start at **Phase 1, Task 1**: Bootstrap FastAPI app named `xyntra`.
4. Deliver `main.py` and `core/config.py`.
5. Proceed task by task.

Do not start Phase 2 until all 13 Phase 1 tasks are complete and verified.

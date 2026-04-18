# Xyntra — Model Router + Project-Aware Execution Layer

> Local-machine-only AI execution control plane. Invoked as `xyntra`.

---

## Product Definition

Xyntra is a backend-first AI execution control plane.  
This is **not** a thin API proxy and **not** a chatbot wrapper.  
This **is** a backend system that makes multiple AI models behave like one consistent, stateful, project-aware execution engine — running entirely on your local machine.

---

## Primary Goals

1. Route across multiple model backends
2. Preserve session continuity regardless of which model is invoked
3. Preserve project-specific working state, not just chat memory
4. Dynamically assemble context
5. Verify outputs before returning when applicable
6. Track artifacts, tasks, decisions, and execution history
7. Support observability, replay, cost controls, privacy controls, and approvals
8. Be modular, production-structured, extensible, and backend-first

---

## Deployment

- **Local machine only** — all infrastructure runs via `docker-compose`
- **Invocation name:** `xyntra`
- **No cloud deployment in V1**
- Outbound API calls go to hosted providers (Anthropic, OpenAI, Gemini, Grok, Mistral, DeepSeek, Groq)
- Local inference via Ollama (runs on-machine)
- Artifact storage: local filesystem (S3-compatible abstraction for future)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | PostgreSQL + pgvector |
| Cache / Queue | Redis |
| Workers | Celery or Dramatiq |
| Validation | Pydantic v2 |
| Observability | OpenTelemetry + structured JSON logging |
| Testing | pytest |
| Linting | ruff + black |
| Containers | Docker + docker-compose |
| Auth | Bearer token / API key (V1), RBAC abstraction ready |

---

## Provider Adapters — V1 (8 adapters, ~94 models)

| # | Provider | Access | Representative Models |
|---|----------|--------|----------------------|
| 1 | Anthropic | API | claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5, claude-3.x series |
| 2 | OpenAI | API | gpt-4o, gpt-4.5, o1, o1-pro, o3, o4-mini, gpt-3.5-turbo |
| 3 | Ollama | Local | llama3.x, qwen2.5, phi4, gemma2, deepseek-r1, codellama, mistral local |
| 4 | Google Gemini | API | gemini-2.5-pro, gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash |
| 5 | xAI Grok | API | grok-3, grok-3-mini, grok-2, grok-2-mini |
| 6 | Mistral | API + Ollama | mistral-large, mistral-small, codestral, mixtral-8x22b, pixtral-large |
| 7 | DeepSeek | API + Ollama | deepseek-chat (V3), deepseek-reasoner (R1), R1 distill variants |
| 8 | Groq | API | llama-3.3-70b, deepseek-r1-distill-llama-70b, gemma2-9b, mixtral-8x7b |

### Full Model Registry (~94 models)

#### Anthropic
| Model | Context |
|-------|---------|
| claude-opus-4-7 | 200K |
| claude-sonnet-4-6 | 200K |
| claude-haiku-4-5 | 200K |
| claude-3-5-sonnet-20241022 | 200K |
| claude-3-5-haiku-20241022 | 200K |
| claude-3-opus-20240229 | 200K |

#### OpenAI
| Model | Context |
|-------|---------|
| gpt-4o | 128K |
| gpt-4o-mini | 128K |
| gpt-4-turbo | 128K |
| gpt-4 | 8K |
| gpt-3.5-turbo | 16K |
| gpt-4.5 | 128K |
| o1 | 200K |
| o1-mini | 128K |
| o1-pro | 200K |
| o3 | 200K |
| o3-mini | 200K |
| o4-mini | 200K |

#### Google Gemini
| Model | Context |
|-------|---------|
| gemini-2.5-pro | 1M |
| gemini-2.0-flash | 1M |
| gemini-2.0-flash-lite | 1M |
| gemini-1.5-pro | 2M |
| gemini-1.5-flash | 1M |
| gemini-1.0-pro | 32K |

#### xAI Grok
| Model | Context |
|-------|---------|
| grok-3 | 131K |
| grok-3-mini | 131K |
| grok-2 | 131K |
| grok-2-mini | 131K |

#### Mistral
| Model | Context |
|-------|---------|
| mistral-large-latest | 128K |
| mistral-small-latest | 128K |
| mistral-nemo | 128K |
| mixtral-8x7b | 32K |
| mixtral-8x22b | 64K |
| codestral-latest | 32K |
| pixtral-large | 128K |

#### DeepSeek
| Model | Context |
|-------|---------|
| deepseek-chat (V3) | 128K |
| deepseek-reasoner (R1) | 128K |
| deepseek-r1:7b | 32K |
| deepseek-r1:14b | 32K |
| deepseek-r1:32b | 32K |
| deepseek-r1:70b | 32K |

#### Meta Llama (via Ollama)
| Model | Context |
|-------|---------|
| llama3.3:70b | 128K |
| llama3.2:90b | 128K |
| llama3.2:11b | 128K |
| llama3.2:3b | 128K |
| llama3.2:1b | 128K |
| llama3.1:405b | 128K |
| llama3.1:70b | 128K |
| llama3.1:8b | 128K |
| llama3:70b | 8K |
| llama3:8b | 8K |
| codellama:70b | 16K |
| codellama:34b | 16K |

#### Qwen / Alibaba (via Ollama)
| Model | Context |
|-------|---------|
| qwen2.5:72b | 128K |
| qwen2.5:32b | 128K |
| qwen2.5:14b | 128K |
| qwen2.5:7b | 128K |
| qwen2.5-coder:32b | 128K |
| qwen2.5-coder:7b | 128K |
| qwq:32b | 32K |

#### Microsoft Phi (via Ollama)
| Model | Context |
|-------|---------|
| phi4:14b | 16K |
| phi3.5:3.8b | 128K |
| phi3:14b | 128K |

#### Google Gemma (via Ollama)
| Model | Context |
|-------|---------|
| gemma2:27b | 8K |
| gemma2:9b | 8K |
| gemma2:2b | 8K |
| gemma:7b | 8K |

#### Groq (fast inference)
| Model | Context |
|-------|---------|
| llama-3.3-70b-versatile | 128K |
| llama-3.1-8b-instant | 128K |
| mixtral-8x7b-32768 | 32K |
| gemma2-9b-it | 8K |
| deepseek-r1-distill-llama-70b | 128K |

---

## Architecture Overview

```
Client
  └── xyntra API (/api/v1/*)
        ├── Auth + Rate Limiting
        ├── Privacy / PII / Injection Guard
        ├── Context Assembly Engine
        │     ├── Semantic Cache (Redis + pgvector)
        │     ├── Memory Layer (session, project, preference, summary)
        │     ├── Token Budget Allocator
        │     └── Retrieval (pgvector)
        ├── Router
        │     ├── Capability Registry (~94 models)
        │     ├── Classifier (task type → candidates)
        │     ├── Strategies (cost / latency / quality / privacy)
        │     ├── Circuit Breaker + Health State
        │     ├── Latency SLA Enforcer
        │     ├── Context Window Auto-Escalator
        │     └── Fallback Chains
        ├── Provider Adapters (8 adapters)
        │     ├── Anthropic
        │     ├── OpenAI
        │     ├── Ollama (local)
        │     ├── Gemini
        │     ├── Grok
        │     ├── Mistral
        │     ├── DeepSeek
        │     └── Groq
        ├── Task Execution Engine
        │     ├── Planner → State Machine → Executor
        │     ├── Verification + Judge Model Hook
        │     ├── Batch Executor
        │     └── Dead Letter Queue
        ├── Artifact Store (local filesystem, versioned)
        ├── Decision + Project State Tracker
        ├── Policy Engine (privacy, cost, approval, guardrails)
        ├── Observability (OTel + structured logs + replay)
        └── Webhook / Event Bus
```

---

## Key Features Above Standard Model Proxies

| Feature | Description |
|---------|-------------|
| **OpenAI-compatible drop-in** | `/v1/chat/completions` — point any OpenAI client at xyntra |
| **Semantic cache** | pgvector similarity lookup before hitting any provider — 40–60% cost reduction |
| **Privacy-first local routing** | `local_only` flag → Ollama only, zero data leaves machine |
| **PII detection + redaction** | Scrub sensitive data before sending to hosted providers |
| **Prompt injection detection** | Block adversarial inputs at ingestion |
| **Context window auto-escalation** | Auto-upgrade model if prompt overflows context limit |
| **Latency SLA enforcement** | Reroute automatically if provider exceeds threshold |
| **Unified tool/function registry** | One tool definition works across all providers |
| **Multi-modal input normalization** | Images, PDFs routed only to capable models |
| **Judge/eval model hook** | Score outputs via second model before accepting |
| **Output comparison mode** | Same prompt → N models in parallel, side-by-side |
| **Conversation branching** | Fork any session at any message |
| **Dead letter queue** | Failed tasks inspectable and retryable, never silently dropped |
| **Webhook / event bus** | Emit events on task complete, approval needed, budget threshold |
| **Prompt template registry** | Versioned, tagged system prompts per project |
| **Spend analytics** | Per-project, per-session, per-model cost breakdown |
| **Per-project token quota** | Hard cap with alerts |
| **API key rotation + expiry** | Security lifecycle management |
| **Local Ollama auto-provisioner** | Auto-pulls required models on startup |
| **Artifact export** | Download session/project state/artifacts as JSON, Markdown, ZIP |
| **Model leaderboard** | Live price/quality matrix across all ~94 models |

---

## Build Phases

| Phase | Name | Key Deliverables |
|-------|------|-----------------|
| 1 | Foundational Backend Skeleton | FastAPI app, Postgres, Redis, Alembic, health endpoints, Docker, Ollama auto-provisioner |
| 2 | Core Data Model | 16 first-class entities including PromptTemplate, SemanticCache, DeadLetter, Webhook, SpendRecord, ToolDefinition |
| 3 | Projects, Sessions, Project State | Full CRUD, structured project state, conversation branching |
| 4 | Memory Layer | Session, project, preference, summary memory; compaction hooks |
| 5 | Provider Abstraction Layer | 8 adapters, multi-modal normalization, unified tool registry |
| 6 | Capability Registry + Router | ~94 models, classifier, strategies, circuit breaker, latency SLA, context auto-escalation |
| 7 | Context Assembly Engine | Selector, ranker, deduper, semantic cache, token budget, pgvector retrieval |
| 8 | Task Graph + Execution Engine | Planner, state machine, task graph, executor, batch executor, DLQ |
| 9 | Verification Layer | Structured output validation, code checks, retry loop, judge model hook |
| 10 | Artifacts + Versioning | Local storage, versioning, diff manager, export (JSON/MD/ZIP) |
| 11 | Decisions + Project Evolution | Decision records, project state updater |
| 12 | Privacy, Cost, Approval Policies | PII redaction, injection guard, content guardrails, privacy routing, token quotas, key rotation |
| 13 | Observability + Replay | OTel tracing, spend analytics, replay API |
| 14 | API Endpoints | All endpoints + OpenAI-compat layer + output comparison + model leaderboard |
| 15 | Developer UX | Seed/bootstrap scripts, curl examples, `xyntra` CLI entrypoint |
| 16 | Testing | Unit, integration, E2E including OpenAI-compat layer tests |
| 17 | Prompt Templates + Analytics + Evals | Template registry, spend dashboard, eval harness, output comparison |
| 18 | Webhooks + Event Bus | Subscription CRUD, event emitter, delivery worker, event log API |
| 19 | Frontend — Core Surfaces | Dashboard, Chat/Inference, Projects, Sessions, Tasks (F-1 to F-5) |
| 20 | Frontend — Model & Routing | Model Leaderboard, Output Comparison, Provider Health, Routing Decision Viewer (F-6 to F-9) |
| 21 | Frontend — Memory & Context | Memory Viewer, Context Assembly Inspector, Semantic Cache Browser (F-10 to F-12) |
| 22 | Frontend — Artifacts & Templates | Artifact Browser, Prompt Template Registry (F-13 to F-14) |
| 23 | Frontend — Analytics & Observability | Spend Dashboard, Trace/Replay Viewer, Event Log (F-15 to F-17) |
| 24 | Frontend — Policies & Admin | Policy Config, Approvals Queue, API Key Manager, Webhook Manager, Eval Harness, Settings (F-18 to F-23) |

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

## Success Criteria for V1

1. Single client calls one backend endpoint family
2. Backend routes between all 8 providers / ~94 models
3. Session continues correctly across provider switches
4. System remembers what user was doing in a specific project
5. Project state is queryable independently of chat
6. Outputs are normalized and stored
7. Tasks can be planned, executed, verified, and tracked
8. Artifacts are versioned and retrievable
9. Routing decisions are observable and replayable
10. Privacy, cost, and approval policies affect behavior
11. Any OpenAI client works against xyntra with zero code changes
12. `local_only` mode sends zero data to hosted providers

---

## Non-Goals (V1)

- No cloud deployment
- No multi-user collaboration
- No repo graph ingestion
- No IDE plugin
- No advanced command execution sandboxes
- No benchmarking harness

---

## Frontend — UI Control Plane (Phase 19+)

23 UI surfaces across 5 functional domains. Built after V1 backend is stable.

**Tech stack (planned):** React + Vite, TypeScript, Tailwind CSS, served locally via docker-compose.

### Core Surfaces

| # | Surface | Description |
|---|---------|-------------|
| F-1 | **Dashboard** | System overview — provider health, active sessions, spend summary, DLQ count |
| F-2 | **Chat / Inference** | Message input, model/strategy selector, streaming response view, conversation branch button |
| F-3 | **Projects** | Project list/create, project state viewer, decisions log timeline |
| F-4 | **Sessions** | Session list per project, threaded conversation view, branch fork UI |
| F-5 | **Tasks** | Task list, state machine status badge, dependency graph, DLQ inspector |

### Model & Routing

| # | Surface | Description |
|---|---------|-------------|
| F-6 | **Model Leaderboard** | ~94-model price/latency/quality matrix, sortable and filterable |
| F-7 | **Output Comparison** | Side-by-side N-model parallel response view for same prompt |
| F-8 | **Provider Health Panel** | Circuit breaker states, per-provider latency/error rates, health indicators |
| F-9 | **Routing Decision Viewer** | Why a model was picked — classifier output, strategy used, fallback chain |

### Memory & Context

| # | Surface | Description |
|---|---------|-------------|
| F-10 | **Memory Viewer** | Session, project, and preference memory — structured readable display |
| F-11 | **Context Assembly Inspector** | What was assembled for a request — ranked chunks, token budget breakdown |
| F-12 | **Semantic Cache Browser** | Cache hit/miss log, similarity scores, cached entry viewer |

### Artifacts & Templates

| # | Surface | Description |
|---|---------|-------------|
| F-13 | **Artifact Browser** | List versioned artifacts, side-by-side diff view, export (JSON/MD/ZIP) |
| F-14 | **Prompt Template Registry** | List/create/edit templates, version diff viewer, rollback, tag/project filter |

### Analytics & Observability

| # | Surface | Description |
|---|---------|-------------|
| F-15 | **Spend Analytics Dashboard** | Per-project/session/model cost charts, token usage over time, quota alerts |
| F-16 | **Trace / Replay Viewer** | OTel span timeline, replay past execution step-by-step |
| F-17 | **Event Log** | Webhook event stream, filterable by type, project, provider |

### Policies & Security

| # | Surface | Description |
|---|---------|-------------|
| F-18 | **Policy Configuration** | PII rules, content guardrails, privacy routing toggles, per-project token quotas |
| F-19 | **Approvals Queue** | Pending approval cards, approve/reject with reason, audit trail |
| F-20 | **API Key Manager** | Create/rotate/expire keys, per-key usage stats, expiry warnings |

### Administration

| # | Surface | Description |
|---|---------|-------------|
| F-21 | **Webhook Manager** | Subscription CRUD, event type selector, delivery log, retry controls |
| F-22 | **Eval Harness** | Run evals against a prompt template, view scored output comparison |
| F-23 | **Settings** | Provider API keys, Ollama model pull UI, system defaults |

**Highest design complexity:** F-7 Output Comparison, F-9 Routing Decision Viewer, F-11 Context Assembly Inspector, F-15 Spend Dashboard, F-16 Trace/Replay — these require custom data visualizations beyond standard CRUD forms.

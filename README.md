# xyntra

> Local-machine AI execution control plane — routes across 8 providers and ~94 models while preserving session continuity, project state, and execution history.

**Status:** Pre-build — spec locked, implementation not started.

---

## What is xyntra?

xyntra is a backend-first AI execution control plane that runs entirely on your local machine.  
It makes multiple AI models behave like one consistent, stateful, project-aware execution engine.

This is **not** a thin proxy. This is **not** a chatbot wrapper.  
This is a production-grade routing and execution layer.

---

## Key Capabilities

- Routes across 8 provider adapters (~94 models) including local Ollama
- OpenAI-compatible drop-in (`/v1/chat/completions`) — point any OpenAI client at xyntra
- Privacy-first `local_only` mode — zero data leaves your machine
- Semantic cache — pgvector similarity lookup before hitting any provider
- PII detection + redaction before sending to hosted providers
- Project-aware memory — system remembers what you were working on
- Session continuity across provider switches
- Task planning, execution, verification, and tracking
- Versioned artifact storage
- Full observability, replay, and cost analytics
- Webhook/event bus for external integrations

---

## Providers

| Provider | Models |
|----------|--------|
| Anthropic | claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5, claude-3.x |
| OpenAI | gpt-4o, gpt-4.5, o1, o3, o4-mini |
| Ollama (local) | llama3.x, qwen2.5, phi4, gemma2, deepseek-r1, codellama |
| Google Gemini | gemini-2.5-pro, gemini-2.0-flash, gemini-1.5-pro |
| xAI Grok | grok-3, grok-3-mini, grok-2 |
| Mistral | mistral-large, codestral, mixtral-8x22b, pixtral |
| DeepSeek | deepseek-chat (V3), deepseek-reasoner (R1) |
| Groq | llama-3.3-70b, deepseek-r1-distill, gemma2, mixtral |

---

## Spec

See [SPEC.md](./SPEC.md) for the full product definition, architecture, feature list, and 127-task build plan across 18 phases.

---

## Stack

Python 3.12 · FastAPI · PostgreSQL + pgvector · Redis · Alembic · SQLAlchemy 2.x · Pydantic v2 · OpenTelemetry · Docker · docker-compose

---

## Implementation

Not started. Build begins at Phase 1.

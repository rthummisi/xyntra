from providers.openai_adapter import OpenAIAdapter


class InklingAdapter(OpenAIAdapter):
    """Inkling (Thinking Machines / Tinker) — OpenAI-compatible API."""

    provider_name = "inkling"
    healthcheck_target = "INKLING_API_KEY"

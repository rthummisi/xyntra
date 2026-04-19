from providers.openai_adapter import OpenAIAdapter


class GrokAdapter(OpenAIAdapter):
    provider_name = "grok"
    healthcheck_target = "GROK_API_KEY"

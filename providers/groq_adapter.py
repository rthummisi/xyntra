from providers.openai_adapter import OpenAIAdapter


class GroqAdapter(OpenAIAdapter):
    provider_name = "groq"
    healthcheck_target = "GROQ_API_KEY"

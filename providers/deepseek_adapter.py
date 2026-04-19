from providers.openai_adapter import OpenAIAdapter


class DeepSeekAdapter(OpenAIAdapter):
    provider_name = "deepseek"
    healthcheck_target = "DEEPSEEK_API_KEY"

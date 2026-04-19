from providers.openai_adapter import OpenAIAdapter


class MistralAdapter(OpenAIAdapter):
    provider_name = "mistral"
    healthcheck_target = "MISTRAL_API_KEY"

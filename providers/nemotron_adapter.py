from providers.openai_adapter import OpenAIAdapter


class NemotronAdapter(OpenAIAdapter):
    """NVIDIA Nemotron — OpenAI-compatible NIM endpoint or api.nvidia.com."""

    provider_name = "nemotron"
    healthcheck_target = "NEMOTRON_API_KEY"

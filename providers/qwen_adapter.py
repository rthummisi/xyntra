from providers.openai_adapter import OpenAIAdapter


class QwenAdapter(OpenAIAdapter):
    """Alibaba Qwen cloud API — OpenAI-compatible via DashScope.
    Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
    Models: qwen-turbo, qwen-plus, qwen-max, qwen2.5-72b-instruct, etc.
    """

    provider_name = "qwen"
    healthcheck_target = "QWEN_API_KEY"

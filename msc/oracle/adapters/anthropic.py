from typing import Any

from anthropic import AsyncAnthropic


class AnthropicAdapter:
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str, 
        base_url: str | None = None,
        capabilities: list[str] | None = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        has_tools: bool = False,
        pricing: dict[str, float] | None = None,
        default_max_tokens: int = 4096,
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking, has_tools)
        self._pricing = pricing or {"input_1m": 0.0, "output_1m": 0.0}
        self.default_max_tokens = default_max_tokens
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url, **kwargs)

    @property
    def pricing(self) -> dict[str, float]:
        return self._pricing

    async def generate(self, prompt: str, image: str | None = None) -> tuple[str, list[Any], dict[str, Any]]:
        content = []
        if image and self.model_info.has_vision:
            if image.startswith("data:"):
                res = image[5:].split(";base64,", 1)
                if len(res) == 2:
                    media_type, data = res
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": data,
                        },
                    })
        
        content.append({"type": "text", "text": prompt})

        from anthropic.types import Message, TextBlock, ToolUseBlock
        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=self.default_max_tokens,
            messages=[{"role": "user", "content": content}],  # type: ignore
            stream=False
        )
        if isinstance(response, Message):
            text_content = "".join([block.text for block in response.content if isinstance(block, TextBlock)])
            
            # 提取原生工具调用
            tool_calls = []
            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    tool_calls.append({
                        "name": block.name,
                        "parameters": block.input
                    })

            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            }
            return text_content, tool_calls, usage
        return "", [], {}

class MagicModelInfo:
    def __init__(self, has_vision: bool, has_thinking: bool, has_tools: bool):
        self._has_vision = has_vision
        self._has_thinking = has_thinking
        self._has_tools = has_tools

    @property
    def has_vision(self) -> bool:
        return self._has_vision

    @property
    def has_thinking(self) -> bool:
        return self._has_thinking

    @property
    def has_tools(self) -> bool:
        return self._has_tools

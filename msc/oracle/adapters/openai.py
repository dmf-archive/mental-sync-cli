from typing import Any

from openai import AsyncOpenAI


class OpenAIAdapter:
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
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking, has_tools)
        self._pricing = pricing or {"input_1m": 0.0, "output_1m": 0.0}
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)

    @property
    def pricing(self) -> dict[str, float]:
        return self._pricing

    async def generate(self, prompt: str, image: str | None = None) -> tuple[str, list[Any], dict[str, Any]]:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image and self.model_info.has_vision:
            content.append({
                "type": "image_url",
                "image_url": {"url": image}
            })

        from openai.types.chat import ChatCompletion
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": content}],  # type: ignore
            stream=False
        )
        if isinstance(response, ChatCompletion):
            usage = {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }
            
            # 提取原生工具调用 (如果存在)
            tool_calls = []
            msg = response.choices[0].message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    try:
                        import json
                        tool_calls.append({
                            "name": tc.function.name,
                            "parameters": json.loads(tc.function.arguments)
                        })
                    except Exception:
                        continue

            return msg.content or "", tool_calls, usage
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

from typing import Any

from google import genai
from google.genai import types


class GeminiAdapter:
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
        vertexai: bool = False,
        pricing: dict[str, float] | None = None,
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking, has_tools)
        self._pricing = pricing or {"input_1m": 0.0, "output_1m": 0.0}
        
        http_options = types.HttpOptions(base_url=base_url) if base_url else None
        self.client = genai.Client(
            api_key=api_key,
            vertexai=vertexai,
            http_options=http_options,
            **kwargs
        )

    @property
    def pricing(self) -> dict[str, float]:
        return self._pricing

    async def generate(self, prompt: str, image: str | None = None) -> tuple[str, list[Any], dict[str, Any]]:
        contents = []
        parts = [types.Part.from_text(text=prompt)]
        
        if image and self.model_info.has_vision:
            if image.startswith("data:"):
                res = image[5:].split(";base64,", 1)
                if len(res) == 2:
                    media_type, data_b64 = res
                    import base64
                    data_bytes = base64.b64decode(data_b64)
                    parts.append(types.Part.from_bytes(data=data_bytes, mime_type=media_type))
            
        contents.append(types.Content(role="user", parts=parts))

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True) if self.model_info.has_thinking else None
            )
        )
        
        # 提取原生工具调用
        tool_calls = []
        if response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.function_call:
                            tool_calls.append({
                                "name": part.function_call.name,
                                "parameters": part.function_call.args
                            })

        usage = {
            "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
        }
        return response.text or "", tool_calls, usage

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

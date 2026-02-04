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
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)

    async def generate(self, prompt: str, image: str | None = None) -> str:
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
            return response.choices[0].message.content or ""
        return ""

class MagicModelInfo:
    def __init__(self, has_vision: bool, has_thinking: bool):
        self._has_vision = has_vision
        self._has_thinking = has_thinking

    @property
    def has_vision(self) -> bool:
        return self._has_vision

    @property
    def has_thinking(self) -> bool:
        return self._has_thinking

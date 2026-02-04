from typing import Any

from anthropic import AsyncAnthropic


class AnthropicAdapter:
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str, 
        base_url: str | None = None,
        capabilities: list[str] = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        default_max_tokens: int = 4096,
        **kwargs: Any
    ):
        self.name = name
        self.model_name = model
        self.capabilities = capabilities or []
        self.model_info = MagicModelInfo(has_vision, has_thinking)
        self.default_max_tokens = default_max_tokens
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url, **kwargs)

    async def generate(self, prompt: str, image: str | None = None) -> str:
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

        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=self.default_max_tokens,
            messages=[{"role": "user", "content": content}],
            stream=False
        )
        text_content = "".join([block.text for block in response.content if block.type == "text"])
        return text_content

class MagicModelInfo:
    def __init__(self, has_vision: bool, has_thinking: bool):
        self.has_vision = has_vision
        self.has_thinking = has_thinking

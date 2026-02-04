from typing import Any

import httpx

from msc.oracle.adapters.openai import OpenAIAdapter


class OpenRouterAdapter(OpenAIAdapter):
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str, 
        base_url: str | None = None,
        capabilities: list[str] = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        **kwargs: Any
    ):
        actual_base_url = base_url or "https://openrouter.ai/api/v1"
        super().__init__(
            name=name,
            model=model,
            api_key=api_key,
            base_url=actual_base_url,
            capabilities=capabilities,
            has_vision=has_vision,
            has_thinking=has_thinking,
            **kwargs
        )
        self.pricing: dict[str, float] = {"input_1m": 0.0, "output_1m": 0.0}

    async def refresh_pricing(self) -> None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://openrouter.ai/api/v1/models")
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    for m in data:
                        if m.get("id") == self.model_name:
                            p = m.get("pricing", {})
                            self.pricing["input_1m"] = round(float(p.get("prompt", 0)) * 1000000, 4)
                            self.pricing["output_1m"] = round(float(p.get("completion", 0)) * 1000000, 4)
                            break
        except Exception:
            pass

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
        capabilities: list[str] | None = None,
        has_vision: bool = False,
        has_thinking: bool = False,
        has_tools: bool = False,
        pricing: dict[str, float] | None = None,
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
            has_tools=has_tools,
            **kwargs
        )
        self._pricing: dict[str, float] = pricing or {"input_1m": 0.0, "output_1m": 0.0}

    @property
    def pricing(self) -> dict[str, float]:
        return self._pricing

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

    async def generate(self, prompt: str, image: str | None = None) -> tuple[str, list[Any], dict[str, Any]]:
        # OpenRouter normalizes the schema to OpenAI format.
        # However, it also provides a 'generation' endpoint to get detailed cost.
        # For the standard chat completion, we use the base OpenAI logic.
        text, tool_calls, usage = await super().generate(prompt, image=image)
        
        # OpenRouter specific: If the response includes 'usage' with 'cost', we should use it.
        # In our current OpenAIAdapter, we only extract tokens.
        # To get the real cost from OpenRouter, we'd ideally check the 'X-OpenRouter-Referrer'
        # or use their specific stats API.
        # For now, we ensure the usage dict is passed through.
        return text, tool_calls, usage

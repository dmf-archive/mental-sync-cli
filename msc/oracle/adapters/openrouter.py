import httpx
from typing import List, Optional, Any, Dict
from msc.oracle.adapters.openai import OpenAIAdapter

class OpenRouterAdapter(OpenAIAdapter):
    """
    专用于 OpenRouter 的适配器，支持价格自动刷新。
    """
    def __init__(
        self, 
        name: str, 
        model: str, 
        api_key: str, 
        base_url: Optional[str] = None,
        capabilities: List[str] = None,
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
        # 存储 $/1M tokens 价格
        self.pricing: Dict[str, float] = {"input_1m": 0.0, "output_1m": 0.0}

    async def refresh_pricing(self) -> None:
        """
        异步刷新 OpenRouter 价格数据。
        遵循用户指令：公开端点绝对不带 key，for better privacy。
        """
        try:
            async with httpx.AsyncClient() as client:
                # OpenRouter 公开端点，不带 Authorization Header
                response = await client.get("https://openrouter.ai/api/v1/models")
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    for m in data:
                        if m.get("id") == self.model_name:
                            p = m.get("pricing", {})
                            # 转换为 $/1M tokens，参考 fetch_models.py:19-20
                            self.pricing["input_1m"] = round(float(p.get("prompt", 0)) * 1000000, 4)
                            self.pricing["output_1m"] = round(float(p.get("completion", 0)) * 1000000, 4)
                            break
        except Exception:
            # 价格刷新失败不应阻塞主流程
            pass

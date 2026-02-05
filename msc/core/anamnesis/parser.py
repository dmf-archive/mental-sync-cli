import json
import re
import uuid
from typing import Any
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    name: str
    parameters: dict[str, Any]
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")

class ToolParser:
    @staticmethod
    def _extract_potential_json(text: str) -> list[str]:
        """使用平衡括号算法提取所有可能的 JSON 块"""
        blocks = []
        
        # 1. 优先提取 ```json ... ``` 块
        code_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        blocks.extend(code_blocks)
        
        # 2. 寻找平衡的 {} 块 (处理裸 JSON)
        stack = []
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        candidate = text[start_idx:i+1]
                        # 避免重复添加已经在 code_blocks 中的内容
                        if not any(candidate in cb for cb in code_blocks):
                            blocks.append(candidate)
        return blocks

    @staticmethod
    def parse(text: str) -> list[ToolCall]:
        tool_calls = []
        blocks = ToolParser._extract_potential_json(text)
        
        for block in blocks:
            try:
                data = json.loads(block)
                if isinstance(data, dict) and "name" in data and "parameters" in data:
                    tool_calls.append(ToolCall(
                        name=data["name"],
                        parameters=data["parameters"]
                    ))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return tool_calls

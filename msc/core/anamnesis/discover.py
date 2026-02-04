import os
from pathlib import Path
from typing import Dict, List

class RulesDiscoverer:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.rule_patterns = [
            ".roo/rules/*.md",
            ".agent/rules/*.md",
            ".msc/rules/*.md",
            "AGENTS.md",
            "CLAUDE.md"
        ]

    def scan(self) -> Dict[str, str]:
        rules = {}
        for pattern in self.rule_patterns:
            # 使用 glob 查找匹配的文件
            for path in self.workspace_root.glob(pattern):
                if path.is_file():
                    try:
                        content = path.read_text(encoding="utf-8")
                        rules[path.name] = content
                    except Exception:
                        # 忽略读取错误
                        continue
        return rules

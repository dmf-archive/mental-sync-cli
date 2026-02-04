from pathlib import Path


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

    def scan(self) -> dict[str, str]:
        rules = {}
        for pattern in self.rule_patterns:
            for path in self.workspace_root.glob(pattern):
                if path.is_file():
                    try:
                        content = path.read_text(encoding="utf-8")
                        rules[path.name] = content
                    except Exception:
                        continue
        return rules

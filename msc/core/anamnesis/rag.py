import re
from pathlib import Path

import yaml

from msc.core.anamnesis.types import AnamnesisConfig, KnowledgeCard


class LiteRAG:
    def __init__(self, config: AnamnesisConfig, project_root: str | None = None, global_root: str | None = None):
        self.config = config
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.global_root = Path(global_root) if global_root else Path.home() / ".msc"

    def search(self, keywords: list[str]) -> list[KnowledgeCard]:
        if not keywords:
            return []

        results: list[KnowledgeCard] = []
        seen_titles: set[str] = set()

        for scope in self.config.search_scope:
            if len(results) >= self.config.max_cards_inject:
                break
                
            base_path = self.project_root if scope == "project" else self.global_root
            cards_dir = base_path / ".msc" / "knowledge-cards"
            
            if not cards_dir.exists():
                continue

            for card_file in cards_dir.glob("*.md"):
                if len(results) >= self.config.max_cards_inject:
                    break
                    
                try:
                    content = card_file.read_text(encoding="utf-8")
                    if any(re.search(re.escape(kw), content, re.IGNORECASE) for kw in keywords):
                        card = self._parse_card(content, str(card_file))
                        if card.title not in seen_titles:
                            results.append(card)
                            seen_titles.add(card.title)
                except Exception:
                    continue

        return results[:self.config.max_cards_inject]

    def _extract_keywords_heuristic(self, context: str) -> list[str]:
        keywords = set()
        keywords.update(re.findall(r'"([^"]+)"', context))
        keywords.update(re.findall(r'`([^`]+)`', context))
        keywords.update(re.findall(r'\b[A-Z][a-zA-Z0-9-]{2,}\b', context))
        
        return list(keywords)

    def _parse_card(self, content: str, path: str) -> KnowledgeCard:
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        if frontmatter_match:
            yaml_content, body = frontmatter_match.groups()
            try:
                meta = yaml.safe_load(yaml_content)
                return KnowledgeCard(
                    title=meta.get("title", Path(path).stem),
                    content=body.strip(),
                    tags=meta.get("tags", []),
                    relevance_score=float(meta.get("relevance_score", 0.0)),
                    path=path
                )
            except Exception:
                pass
        
        return KnowledgeCard(title=Path(path).stem, content=content.strip(), path=path)

import re
import yaml
from pathlib import Path
from typing import List, Dict, Set, Optional
from msc.core.anamnesis.types import AnamnesisConfig, KnowledgeCard

class LiteRAG:
    def __init__(self, config: AnamnesisConfig, project_root: Optional[str] = None, global_root: Optional[str] = None):
        self.config = config
        self.project_root = Path(project_root) if project_root else Path.cwd()
        # 默认全局路径，实际应从环境变量或配置获取
        self.global_root = Path(global_root) if global_root else Path.home() / ".msc"

    def search(self, keywords: List[str]) -> List[KnowledgeCard]:
        if not keywords:
            return []

        results: List[KnowledgeCard] = []
        seen_titles: Set[str] = set()

        # 按照 search_scope 顺序检索
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
                    # 简单的关键词匹配 (Grep 模拟)
                    if any(re.search(re.escape(kw), content, re.IGNORECASE) for kw in keywords):
                        card = self._parse_card(content, str(card_file))
                        if card.title not in seen_titles:
                            results.append(card)
                            seen_titles.add(card.title)
                except Exception:
                    continue

        return results[:self.config.max_cards_inject]

    def _extract_keywords_heuristic(self, context: str) -> List[str]:
        keywords = set()
        # 1. 引号内的词
        keywords.update(re.findall(r'"([^"]+)"', context))
        # 2. 反引号内的词
        keywords.update(re.findall(r'`([^`]+)`', context))
        # 3. 大写缩写或驼峰命名 (简单启发式)
        keywords.update(re.findall(r'\b[A-Z][a-zA-Z0-9-]{2,}\b', context))
        
        return list(keywords)

    def _parse_card(self, content: str, path: str) -> KnowledgeCard:
        # 简单的 Frontmatter 解析
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

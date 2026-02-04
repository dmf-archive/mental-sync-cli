import tempfile
from pathlib import Path

from msc.core.anamnesis.discover import RulesDiscoverer


def test_discover_finds_roo_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        rules_dir = tmp_path / ".roo" / "rules"
        rules_dir.mkdir(parents=True)
        
        rule_file = rules_dir / "test-rule.md"
        rule_file.write_text("# Test Rule Content", encoding="utf-8")
        
        discoverer = RulesDiscoverer(workspace_root=tmpdir)
        rules = discoverer.scan()
        
        assert "test-rule.md" in rules
        assert rules["test-rule.md"] == "# Test Rule Content"

def test_discover_finds_agents_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("# Agents Contract", encoding="utf-8")
        
        discoverer = RulesDiscoverer(workspace_root=tmpdir)
        rules = discoverer.scan()
        
        assert "AGENTS.md" in rules
        assert rules["AGENTS.md"] == "# Agents Contract"

def test_discover_handles_nested_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # .agent/rules/
        agent_rules = tmp_path / ".agent" / "rules"
        agent_rules.mkdir(parents=True)
        (agent_rules / "agent-rule.md").write_text("Agent Rule", encoding="utf-8")
        
        discoverer = RulesDiscoverer(workspace_root=tmpdir)
        rules = discoverer.scan()
        
        assert "agent-rule.md" in rules
        assert rules["agent-rule.md"] == "Agent Rule"

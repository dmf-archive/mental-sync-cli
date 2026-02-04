# Implementation Plan: Anamnesis Engine & Context Management

## 1. 目标

实现 MSC v3.0 的认知核心 Anamnesis，支持 8-Section 上下文布局、Lite RAG 潜意识注入以及环境元数据管理。

## 2. 目录结构

```text
msc/
├── core/
│   ├── anamnesis/
│   │   ├── __init__.py
│   │   ├── context.py      # 上下文组装工厂 (ContextFactory)
│   │   ├── metadata.py     # 元数据采集与状态管理
│   │   ├── rag.py          # Lite RAG (Grep-based) 检索逻辑
│   │   ├── discover.py     # 项目规则 (.roo, .agent, etc.) 扫描器
│   │   ├── compress.py     # Token 溢出压缩策略
│   │   └── types.py        # Anamnesis 专用类型定义
│   ├── subagent/
│   │   ├── __init__.py
│   │   ├── base.py         # Sub-agent 基类
│   │   ├── organizer.py    # 知识蒸馏 Organizer 实现
│   │   └── green_tea.py    # 凭证隔离 Green TEA 实现
│   └── tools/
│       └── notebook.py     # memory_add/replace/del 工具实现
```

## 3. 核心组件设计

### 3.1 ContextFactory (context.py)

- 负责按 8-Section 顺序组装最终的 System Prompt。
- 维护 `step` 计数器，触发 `rag.py` 的潜意识注入。
- 集成 `compress.py` 进行实时 Token 监控。

### 3.2 Metadata Provider (metadata.py)

- 采集系统状态：时间、路径、活动终端、资源配额。
- 注入 PFMS 成本元数据。

### 3.3 Lite RAG (rag.py)

- 实现 `heuristic` 关键词提取（Regex）。
- 实现 `self_extract` 关键词提取（LLM 辅助）。
- 执行分层 Grep 检索（Project -> Global）。

### 3.4 Rules Discoverer (discover.py)

- 递归扫描工作区，识别并读取 `.roo/rules/`, `.agent/rules/`, `AGENTS.md` 等。

## 4. 实施步骤 (TDD 驱动)

### Phase 1: 基础类型与元数据 (Code Mode)

1. 定义 `msc/core/anamnesis/types.py`。
2. 实现 `msc/core/anamnesis/metadata.py` 并编写单元测试。

### Phase 2: 规则扫描与 RAG (Code Mode)

1. 实现 `msc/core/anamnesis/discover.py`，验证多框架规则兼容性。
2. 实现 `msc/core/anamnesis/rag.py`，测试 Grep 检索准确性。

### Phase 3: 上下文组装与压缩 (Code Mode)

1. 实现 `msc/core/anamnesis/context.py`。
2. 实现 `msc/core/anamnesis/compress.py`。

### Phase 4: 工具与 Sub-agent (Code Mode)

1. 实现 `msc/core/tools/notebook.py`。
2. 搭建 `msc/core/subagent/` 基础框架。

## 5. 验收标准

- [ ] 成功组装包含 8 个 Section 的 System Prompt。
- [ ] 模拟 5 个 step 后，成功触发 Lite RAG 注入。
- [ ] 规则扫描器能正确识别 `.roo/rules/` 下的文件。
- [ ] 所有核心逻辑通过 `pytest` 覆盖。

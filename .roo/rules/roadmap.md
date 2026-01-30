---
title: "Mental-Sync-CLI (MSC) 路线图与待办清单"
version: "1.0.0"
status: "Official"
author: "Chain://Research"
last_updated: "2026-01-29"
---

# Mental-Sync-CLI (MSC) 路线图与待办清单

> "The path from chaos to order: Engineering the cognitive bridge."

## 1. 实施路线图 (Roadmap)

### Phase 1: Foundation (骨架搭建)

**目标**: 建立可运行的 CLI 框架，打通开发流程。

- **Task 1.1**: 项目初始化 (目录结构, `pyproject.toml`, CI/CD)。
- **Task 1.2**: CLI 框架实现 (Typer 主命令, version, config)。
- **Task 1.3**: 日志与配置系统 (Loguru, Pydantic)。
- **Task 1.4**: Wire 协议原型 (基础数据结构, 内存消息总线)。

### Phase 2: Core Logic (核心逻辑)

**目标**: 实现智能体核心循环，能够执行简单对话。

- **Task 2.1**: Agent Core 抽象与实现 (EchoCore, LLMCore)。
- **Task 2.2**: TUI 界面开发 (Rich 实时显示 Thought/Message)。
- **Task 2.3**: 基础工具集 (Tool 注册装饰器, 文件操作工具)。

### Phase 3: Security & Sandbox (安全沙箱)

**目标**: 引入安全隔离机制，保护宿主环境。

- **Task 3.1**: 沙箱管理器抽象 (SandboxManager)。
- **Task 3.2**: 权限管理与审批流 (PermissionManager, ApprovalRequest)。
- **Task 3.3**: 平台特定沙箱实现 (Linux Landlock, Windows RestrictedToken)。

### Phase 4: Cognition & Evolution (认知进化)

**目标**: 增强智能体的记忆和自我优化能力。

- **Task 4.1**: Context Manager (会话历史, Token 截断)。
- **Task 4.2**: Knowledge Base (Markdown 知识库, 关键词检索)。
- **Task 4.3**: Organizer (日志分析, Daily Summary 自动生成)。

---

## 2. 待办清单 (Todo List)

### [ ] Phase 1: Foundation

- [ ] 初始化标准目录结构 (`src/msc`, `tests`, `.roo`)
- [ ] 配置 `pyproject.toml` (Ruff, Mypy, Pytest)
- [ ] 实现 `msc` 主入口及基础子命令
- [ ] 集成结构化日志系统
- [ ] 定义 `WireMessage` Pydantic 模型

### [ ] Phase 2: Core Logic

- [ ] 实现 `Agent Core` 决策循环接口
- [ ] 接入 OpenAI/Anthropic API 适配器
- [ ] 开发基于 `Rich` 的 TUI 交互界面
- [ ] 实现工具注册装饰器及基础文件工具

### [ ] Phase 3: Security & Sandbox

- [ ] 实现 `SandboxManager` 基础架构
- [ ] 开发 TUI 审批交互流程
- [ ] 实现基础路径检查与白名单过滤
- [ ] 调研并集成平台原生隔离技术

### [ ] Phase 4: Cognition & Evolution

- [ ] 实现会话上下文自动压缩与管理
- [ ] 建立基于 Markdown 的本地知识库索引
- [ ] 编写 `Reflect-Agent` 自动化日志分析脚本
- [ ] 完善 `Flow` 状态机技能系统

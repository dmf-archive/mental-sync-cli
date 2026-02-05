# Mental-Sync-CLI (MSC) Roadmap

> "From a sci-fi scaffold to a sovereign cognitive runtime."

## 1. 当前里程碑：Phase 1 - Foundation (已完成/进行中)

### 1.1 核心架构 (Core Architecture)

- [x] **Orchestration Gateway (OG)**: 实现基础的 Session 管理与认知循环 (`msc/core/og.py`)。
- [x] **Anamnesis (Context Manager)**: 实现动态上下文组装、Metadata 收集与 Rules 发现 (`msc/core/anamnesis/`)。
- [x] **Oracle (PFMS)**: 实现跨 Provider 的逻辑模型路由与故障转移 (`msc/oracle/`)。

### 1.2 安全沙箱 (NFSS v2.0)

- [x] **Windows Sandbox**: 实现基于 Restricted Token 和 Job Object 的原生隔离 (`msc/core/tools/sandbox_launcher.py`)。
- [x] **Network Blocking**: 实现基于 Windows Firewall COM 接口的动态出站拦截。
- [x] **Privilege Stripping**: 验证管理员权限剥离与 `deny only` 状态。

### 1.3 基础工具集 (Minimal Tool Set)

- [x] **Execute**: 支持沙箱化执行系统命令 (`msc/core/tools/system_ops.py`)。
- [x] **Create Agent**: 已实现基于协程上下文的子代理派生与消息传递逻辑 (`msc/core/og.py`, `msc/core/tools/agent_ops.py`)。
- [ ] **Write/Diff**: (待增强) 实现原子写入与备份机制。

---

## 2. 下一阶段：Phase 2 - Cognitive Sovereignty (短期目标)

### 2.1 核心工具集补完 (Core Toolset Completion)

- [ ] **Atomic File Ops**: 完善 `write_file` 与 `apply_diff`，集成自动备份与回滚。
- [ ] **Structured List**: 实现 `list_files` 的高性能 JSON 输出，支持大规模目录树。
- [ ] **Memory CRUD**: 实现 `memory` 工具，允许 Agent 声明式管理其 Notebook (Hot Memory)。

### 2.2 跨平台沙箱 (Cross-platform NFSS)

- [x] **Windows Sandbox**: 基于 Restricted Token 和 Job Object 的原生隔离已初步实现 (`msc/core/tools/sandbox_launcher.py`)。
- [-] **Linux (bwrap)**: 已实现 `LinuxSandbox` 适配器，支持基础的命名空间隔离 (`msc/core/tools/system_ops.py`)。
- [-] **macOS (Seatbelt)**: 已实现 `MacOSSandbox` 适配器，支持基础的 `sandbox-exec` 配置文件生成 (`msc/core/tools/system_ops.py`)。

### 2.3 认知增强 (Cognitive Enhancement)

- [x] **Lite RAG**: 已实现基于启发式关键词提取的知识卡片检索机制 (`msc/core/anamnesis/rag.py`)。
- [x] **Gas Metering**: 已在 `OG` 层级实现基础的 Gas 计费与元数据追踪逻辑 (`msc/core/og.py`, `msc/core/anamnesis/metadata.py`)。
- [ ] **Organizer Agent**: 实现专门用于“记忆蒸馏”的特殊 Sub-agent。

---

## 3. 远期愿景：Phase 3 - The World Computer (长期目标)

### 3.1 叙事集成 (Narrative Integration)

- [-] **Gas Metering**: 已实现后端逻辑，待在 TUI 中实时显示。

### 3.2 基础设施 (Infrastructure)

- [ ] **Bridge Layer**: 实现轻量级 JSON-RPC 总线，支持 Web UI 接入。
- [ ] **OSPU Integration**: 探索与全同态加密 (FHE) 状态机的集成，实现逻辑根信任。

---

## 4. 待修复与优化 (Bugs & Debt)

- [x] 修复 `agent_ops.py` 中的权限越权漏洞，强制执行 ACL 继承。
- [x] 强化 `sandbox_launcher.py` 的 Windows 安全实现，移除 Breakaway 权限并增加 Job 限制。
- [x] 实现真实的 Gas 计费逻辑，支持从 Oracle 适配器透传 usage 和 pricing 元数据。
- [ ] 增强 `MetadataProvider` 在非 Windows 系统下的进程检测。
- [ ] `AnthropicAdapter` 支持多图输入。
- [ ] 优化 `ToolParser` 的正则匹配，提高对非标准 JSON 的容错性。

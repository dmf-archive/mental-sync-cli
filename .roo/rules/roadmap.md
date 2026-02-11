# Mental-Sync-CLI (MSC) Roadmap

> "From a sci-fi scaffold to a sovereign cognitive runtime."

## 1. 当前里程碑：Phase 1 - Foundation (已完成/进行中)

### 1.1 核心架构 (Core Architecture)

- [x] **Orchestration Gateway (OG)**: 实现基础的 Session 管理与认知循环 (`msc/core/og.py`)。
  - **DEBT**: `og.py` 仍残留硬编码的 `mode_instruction`，需迁移至 `context.py`。
- [x] **Anamnesis (Context Manager)**: 实现动态上下文组装、Metadata 收集与 Rules 发现 (`msc/core/anamnesis/`)。
  - **CRITICAL**: 内部协议 V2 -> V3 演进导致 17+ 单元测试失败。
  - **ACTION**: 废弃 `tests/core/test_tools.py`，将其功能整合至 `tests/core/test_agent_ops.py`。
  - **ACTION**: 废弃 `tests/core/test_subagent_flow.py`，其逻辑已由 `tests/core/test_subagent_e2e.py` 覆盖。
- [x] **Oracle (PFMS)**: 实现跨 Provider 的逻辑模型路由与故障转移 (`msc/oracle/`)。
  - **CRITICAL**: 修复 `Oracle` 与 `Adapter` 间的返回值解构协议 (3 vs 4 items) 不一致问题。

### 1.2 安全沙箱 (NFSS v2.0)

- [x] **Windows Sandbox**: 实现基于 Restricted Token 和 Job Object 的原生隔离 (`msc/core/tools/sandbox_launcher.py`)。
- [x] **Network Blocking**: 实现基于 Windows Firewall COM 接口的动态出站拦截。
- [x] **Privilege Stripping**: 验证管理员权限剥离与 `deny only` 状态。

### 1.3 基础工具集 (Minimal Tool Set)

- [x] **Execute**: 支持沙箱化执行系统命令 (`msc/core/tools/system_ops.py`)。
- [x] **Create Agent**: 已实现基于协程上下文的子代理派生与消息传递逻辑。
  - **CHANGE**: 返回值已从 `str` 变更为 `dict`，需更新相关测试。
- [x] **Complete Task**: 统一协议，移除 `status` 参数，仅保留 `summary`。

---

## 2. 下一阶段：Phase 2 - Cognitive Sovereignty (短期目标)

### 2.1 协议稳定性与测试重构 (Protocol Stability & Test Refactoring)

- [ ] **Test Alignment**: 修复所有失败的单元测试，确保 V3 协议在全链路闭环。
- [ ] **Test Consolidation**:
  - 整合 `test_agent_ops.py` 与 `test_tools.py`。
  - 整合 `test_subagent_flow.py` 与 `test_subagent_e2e.py`。
- [ ] **Schema Enforcement**: 引入 Pydantic 严格校验工具调用与返回值的 Schema。

### 2.2 核心工具集补完 (Core Toolset Completion)

- [ ] **Atomic File Ops**: 完善 `write_file` 与 `apply_diff`，集成自动备份与回滚。
- [ ] **Structured List**: 实现 `list_files` 的高性能 JSON 输出，支持大规模目录树。
- [ ] **Memory CRUD**: 实现 `memory` 工具，允许 Agent 声明式管理其 Notebook (Hot Memory)。

### 2.3 CLI 接口实现 (Interface Layer)

- [ ] **MSC CLI Entry**: 基于 `Typer` + `Rich` 实现首个可运作的终端交互界面。
- [ ] **Session Persistence**: 实现 Session 的持久化存储与断点续传。

---

## 3. 远期愿景：Phase 3 - The World Computer (长期目标)

### 3.1 认知增强 (Cognitive Enhancement)

- [ ] **Organizer Agent**: 实现专门用于“记忆蒸馏”的特殊 Sub-agent。
- [ ] **Lite RAG Optimization**: 优化启发式关键词提取算法，降低 Token 消耗。

### 3.2 基础设施 (Infrastructure)

- [ ] **Bridge Layer**: 实现轻量级 JSON-RPC 总线，支持 Web UI 接入。
- [ ] **OSPU Integration**: 探索与全同态加密 (FHE) 状态机的集成，实现逻辑根信任。

---

## 4. 待修复与优化 (Bugs & Debt)

- [x] 修复 `agent_ops.py` 中的权限越权漏洞，强制执行 ACL 继承。
- [x] 强化 `sandbox_launcher.py` 的 Windows 安全实现。
- [x] 实现真实的 Gas 计费逻辑。
- [ ] **URGENT**: 修复 `Oracle` 与 `Adapter` 间的返回值解构错误。
- [ ] 增强 `MetadataProvider` 在非 Windows 系统下的进程检测。
- [ ] `AnthropicAdapter` 支持多图输入。

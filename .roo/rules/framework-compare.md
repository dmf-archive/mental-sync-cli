# Code Agent 框架深度对比：kimi-cli vs. codex

本文档旨在深度剖析 `kimi-cli` 与 `codex` 的架构设计、工具管理及核心能力，为 `Mental-Sync-CLI` 的设计提供参考。

## 1. 核心架构与技术栈

### kimi-cli
- **核心语言**: Python 3.12+
- **UI 框架**: Typer + Rich (TUI)
- **异步运行时**: asyncio
- **LLM 抽象层**: `kosong` (统一多模型接口)
- **OS 交互层**: `kaos` (支持本地/SSH 远程执行)
- **包管理**: uv

### codex
- **核心语言**: Rust
- **UI 框架**: Ratatui (TUI)
- **异步运行时**: tokio
- **LLM 抽象层**: 自研 `protocol` + `openai-models`
- **OS 交互层**: `exec-server` (POSIX/Windows)
- **包管理**: cargo + bazel

## 2. 内置工具集 (Built-in Tools)

### kimi-cli (Python 模块化)

- **核心抽象**: `kosong` (LLM Provider 抽象) 与 `kaos` (OS 交互抽象)。
- **工具实现**: 基于 `SimpleToolset` 管理 `CallableTool`，支持并发执行。
- **文件操作**: `ReadFile`, `WriteFile`, `StrReplaceFile`, `Glob`, `Grep`。
- **系统交互**: `Shell` (通过 `kaos` 实现，支持本地/SSH 远程执行)。
- **元能力**: `Task` (派生子 Agent), `Think` (记录思考过程), `SetTodoList`。
- **特殊能力**: `SendDMail` (跨检查点回滚/通信)。

### codex (Rust 强类型)

- **执行引擎**: 深度集成的 `exec-server`，支持多平台沙箱。
- **沙箱实现**:
  - **Linux**: 基于 Landlock + seccomp 实现细粒度权限控制。
  - **macOS**: 基于 `sandbox-exec` (Seatbelt) 策略文件。
  - **Windows**: 支持 `RestrictedToken` 和 `Elevated` 两种沙箱级别。
- **动态工具**: 通过 `DynamicToolSpec` 协议支持运行时定义工具 Schema，利用 JSON-RPC 进行异步分发。
- **规划工具**: `plan_tool` 专门用于任务步骤管理。

## 3. Skills 管理机制

### kimi-cli: 声明式 Markdown

- **定义方式**: 每个 Skill 是一个文件夹，包含 `SKILL.md`。
- **元数据**: 通过 Frontmatter 定义 `name`, `description`, `type` (standard/flow)。
- **流程控制**: 支持在 `SKILL.md` 中嵌入 `mermaid` 或 `d2` 图表来定义 `Flow`（状态机任务流）。
- **加载逻辑**: 扫描 `~/.config/agents/skills` 或项目本地 `.agents/skills`。

### codex: 结构化加载与注入

- **定义方式**: 同样采用 `SKILL.md` (YAML Frontmatter) + `SKILL.json` (元数据与依赖)。
- **层级加载**: 支持 `Repo` (项目级)、`User` (用户级)、`System` (系统内置) 和 `Admin` (全局配置) 四种作用域。
- **依赖管理**: 显式声明工具依赖（如 `mcp`, `env_var`, `cli`），支持自动注入到 Prompt。
- **缓存机制**: `SkillsManager` 提供基于 CWD 的缓存，支持 `force_reload`。

## 4. 热重载 (Hot Reload) 深度调研

### kimi-cli (基于异常捕获的粗粒度重载)

- **实现机制**:
  - 定义了 `Reload` 异常类。
  - 在 `cli/__init__.py` 的 `_reload_loop` 中使用 `while True` 包裹 `_run` 函数。
  - 当 UI 层（如 `slash.py` 中的 `/reload` 或 `/clear` 命令）抛出 `Reload` 异常时，外层循环捕获异常并重新进入 `_run`，从而实现配置和环境的重新初始化。
- **Tools 级别**:
  - 在 `soul/toolset.py` 中通过 `importlib.import_module` 动态加载工具。
  - 每次 `Reload` 触发时，会重新调用 `load_tools`，但由于 Python 的模块缓存机制，若不显式调用 `importlib.reload`，已加载的模块代码不会更新。
- **Skills 级别**: 每次执行任务时动态读取 `SKILL.md`，天然支持内容热更新。

### codex (基于缓存失效的细粒度重载)

- **实现机制**:
  - `SkillsManager` 维护了一个基于当前工作目录 (CWD) 的缓存 `cache_by_cwd`。
  - 提供 `clear_cache()` 方法直接清空所有缓存。
  - `skills_for_cwd` 方法接受 `force_reload` 参数，若为 `true` 则跳过缓存重新扫描文件系统。
- **Tools 级别**:
  - 静态工具在编译时确定。
  - 动态工具通过 `DynamicToolSpec` 协议在运行时定义，支持通过 JSON-RPC 动态更新工具定义。

### 理想目标：全量热重载 (Full Hot Reload)

对于 `Mental-Sync-CLI`，我们需要实现：

1. **工具热重载**: 改进 `kimi-cli` 的模式，在加载工具前检测文件变更，并使用 `importlib.reload` 强制刷新模块。
2. **Prompt 热重载**: 借鉴 `codex` 的 `force_reload` 思想，结合 `watchdog` 监控 `system.md` 或 `SKILL.md`，实现变更即生效。
3. **状态保持重载**: 优化 `kimi-cli` 的 `Reload` 异常机制，在重载时序列化当前 `Session` 状态，确保重载后能恢复到之前的对话上下文。

## 5. 总结与启示

1. **去魅的架构**: 学习 `kimi-cli` 将科幻概念（D-Mail, Soul）映射到具体工程实现（Checkpoint, Loop）的方法。
2. **安全第一**: 借鉴 `codex` 的沙箱设计，尤其是对多平台的适配和 `Landlock` 的应用。
3. **自举的关键**: `kimi-cli` 的 `Flow` 机制和 `SendDMail` 为 Agent 的自我纠错和复杂规划提供了极好的范式。

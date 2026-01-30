# Reference Project: Codex

> "安全第一：基于沙箱的强类型工具管理。"

## 1. 核心架构与技术栈

- **核心语言**: Rust
- **UI 框架**: Ratatui (TUI)
- **异步运行时**: tokio
- **LLM 抽象层**: 自研 `protocol` + `openai-models`
- **OS 交互层**: `exec-server` (POSIX/Windows)
- **包管理**: cargo + bazel

## 2. 内置工具集 (Built-in Tools)

- **执行引擎**: 深度集成的 `exec-server`，支持多平台沙箱。
- **沙箱实现**:
  - **Linux**: 基于 Landlock + seccomp 实现细粒度权限控制。
  - **macOS**: 基于 `sandbox-exec` (Seatbelt) 策略文件。
  - **Windows**: 支持 `RestrictedToken` 和 `Elevated` 两种沙箱级别。
- **动态工具**: 通过 `DynamicToolSpec` 协议支持运行时定义工具 Schema，利用 JSON-RPC 进行异步分发。
- **规划工具**: `plan_tool` 专门用于任务步骤管理。

## 3. Skills 管理机制：结构化加载与注入

- **定义方式**: `SKILL.md` (YAML Frontmatter) + `SKILL.json` (元数据与依赖)。
- **层级加载**: 支持 `Repo` (项目级)、`User` (用户级)、`System` (系统内置) 和 `Admin` (全局配置) 四种作用域。
- **依赖管理**: 显式声明工具依赖（如 `mcp`, `env_var`, `cli`），支持自动注入到 Prompt。
- **缓存机制**: `SkillsManager` 提供基于 CWD 的缓存，支持 `force_reload`。

## 4. 热重载 (Hot Reload)

- **实现机制**: 基于缓存失效的细粒度重载。
  - `SkillsManager` 维护了一个基于当前工作目录 (CWD) 的缓存 `cache_by_cwd`。
  - 提供 `clear_cache()` 方法直接清空所有缓存。
  - `skills_for_cwd` 方法接受 `force_reload` 参数，若为 `true` 则跳过缓存重新扫描文件系统。
- **Tools 级别**: 静态工具在编译时确定。动态工具通过 `DynamicToolSpec` 协议在运行时定义，支持通过 JSON-RPC 动态更新工具定义。

## 5. 总结与启示

1. **安全沙箱**: 借鉴其对多平台的适配和 `Landlock` 的应用，确保 Agent 执行环境的安全性。
2. **强类型约束**: 结构化的 Skill 定义和依赖管理，提高了系统的鲁棒性。

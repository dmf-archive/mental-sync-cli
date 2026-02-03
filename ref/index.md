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

# Reference Project: kimi-cli

> "将科幻概念映射到具体工程实现。"

## 1. 核心架构与技术栈

- **核心语言**: Python 3.12+
- **UI 框架**: Typer + Rich (TUI)
- **异步运行时**: asyncio
- **LLM 抽象层**: `kosong` (统一多模型接口)
- **OS 交互层**: `kaos` (支持本地/SSH 远程执行)
- **包管理**: uv

## 2. 内置工具集 (Built-in Tools)

- **核心抽象**: `kosong` (LLM Provider 抽象) 与 `kaos` (OS 交互抽象)。
- **工具实现**: 基于 `SimpleToolset` 管理 `CallableTool`，支持并发执行。
- **文件操作**: `ReadFile`, `WriteFile`, `StrReplaceFile`, `Glob`, `Grep`。
- **系统交互**: `Shell` (通过 `kaos` 实现，支持本地/SSH 远程执行)。
- **元能力**: `Task` (派生子 Agent), `Think` (记录思考过程), `SetTodoList`。
- **特殊能力**: `SendDMail` (跨检查点回滚/通信)。

## 3. Skills 管理机制：声明式 Markdown

- **定义方式**: 每个 Skill 是一个文件夹，包含 `SKILL.md`。
- **元数据**: 通过 Frontmatter 定义 `name`, `description`, `type` (standard/flow)。
- **流程控制**: 支持在 `SKILL.md` 中嵌入 `mermaid` 或 `d2` 图表来定义 `Flow`（状态机任务流）。
- **加载逻辑**: 扫描 `~/.config/agents/skills` 或项目本地 `.agents/skills`。

## 4. 热重载 (Hot Reload)

- **实现机制**: 基于异常捕获的粗粒度重载。
  - 定义了 `Reload` 异常类。
  - 在 `cli/__init__.py` 的 `_reload_loop` 中使用 `while True` 包裹 `_run` 函数。
  - 当 UI 层抛出 `Reload` 异常时，外层循环捕获异常并重新进入 `_run`，从而实现配置和环境的重新初始化。
- **Tools 级别**: 在 `soul/toolset.py` 中通过 `importlib.import_module` 动态加载工具。每次 `Reload` 触发时重新调用 `load_tools`。
- **Skills 级别**: 每次执行任务时动态读取 `SKILL.md`，天然支持内容热更新。

## 5. 总结与启示

1. **概念映射**: 学习其将科幻概念（D-Mail, Soul）映射到具体工程实现（Checkpoint, Loop）的方法。
2. **自举能力**: `Flow` 机制和 `SendDMail` 为 Agent 的自我纠错和复杂规划提供了极好的范式。

# Reference Project: NanoClaw

> "Small enough to understand. Secure by isolation."

## 1. 核心架构与技术栈

- **核心语言**: TypeScript (Node.js 20+)
- **容器技术**: Apple Container (macOS 原生 Linux VM 隔离)
- **Agent SDK**: `@anthropic-ai/claude-agent-sdk`
- **通信协议**: WhatsApp (baileys) + 文件系统 IPC
- **存储**: SQLite (better-sqlite3)

## 2. 隔离与安全模型

NanoClaw 的核心竞争力在于其**物理隔离**机制：

- **容器化运行**: 每个群组或任务都在独立的 Apple Container 实例中运行，而非宿主进程。
- **最小化挂载**: 容器仅挂载该群组对应的 `groups/{folder}` 目录，Agent 无法访问其他群组的数据。
- **非特权执行**: 容器内以 `node` 用户运行，Bash 访问被限制在容器沙箱内。
- **环境变量隔离**: 仅将必要的 Auth Token (`CLAUDE_CODE_OAUTH_TOKEN` 或 `ANTHROPIC_API_KEY`) 注入容器。

## 3. IPC 机制：基于文件系统的命名空间

NanoClaw 巧妙地利用文件系统实现了异步、安全的 IPC：

- **目录结构**: `data/ipc/{group_folder}/[messages|tasks]/`
- **单向写入**: Agent 在容器内向挂载的 IPC 目录写入 JSON 文件。
- **宿主审计**: 宿主进程 ([`src/index.ts`](ref/nanoclaw/src/index.ts)) 轮询这些目录，并根据目录名（即群组身份）进行权限校验。
- **能力暴露**: 通过内置的 `nanoclaw` MCP 服务器暴露 `send_message` 和 `schedule_task` 等工具。

## 4. 记忆系统：分层 CLAUDE.md

- **Global Memory**: `groups/CLAUDE.md` (所有群组只读，Main 频道可写)。
- **Group Memory**: `groups/{name}/CLAUDE.md` (群组私有，读写)。
- **自动加载**: 利用 Claude Agent SDK 的 `settingSources: ['project']` 特性自动向上递归加载 `CLAUDE.md`。

## 5. 任务调度 (Task Scheduler)

- **实现**: [`src/task-scheduler.ts`](ref/nanoclaw/src/task-scheduler.ts) 负责轮询数据库中的到期任务。
- **执行**: 任务被视为一个“无输入”的 Agent 调用，运行在对应的群组容器上下文中。
- **模式**: 支持 `cron`、`interval` 和 `once`。

## 6. 总结与启示

1. **极简主义**: 整个核心逻辑仅由少数几个 TypeScript 文件组成，极易审计和定制。
2. **AI-Native 定制**: 提倡通过 Claude Code 运行 Skill ([`.claude/skills/`](ref/nanoclaw/.claude/skills/)) 来修改代码，而非通过复杂的配置文件。
3. **安全基准**: 为 MSC 的沙箱设计提供了优秀的参考范式，特别是基于文件系统命名空间的 IPC 审计逻辑。

# Reference Project: OpenClaw (OpenClawd)

> "I can run local, remote, or purely on vibes—results may vary with DNS."

## 1. 核心定位与架构

OpenClaw 是一个基于 Node.js 的个人 AI 助手框架，强调多渠道接入（WhatsApp, Telegram, Discord 等）和跨设备能力。

- **核心语言**: TypeScript (Node.js 22+)
- **架构模式**: Local-first Gateway (控制平面) + WebSocket 协议。
- **通信协议**: 自研 WebSocket 协议 + ACP (Agent Client Protocol) 桥接。
- **运行环境**: 宿主环境直接运行，支持 Docker 沙箱（非主会话可选）。

## 2. 关键技术特性

### 2.1 跨设备工具调用 (Nodes)

OpenClaw 通过 `node.invoke` 机制，允许 Gateway 调用已配对的移动端（iOS/Android）或 macOS 节点的硬件功能：

- 摄像头快照/录像。
- 地理位置获取。
- 系统通知与本地命令执行 (`system.run`)。

### 2.2 Skills 与自举 (Self-Bootstrapping)

- **定义**: 使用 `SKILL.md` 配合 JSON5 Frontmatter。
- **Reflect-Agent**: 内置元认知循环，通过分析 `Inference Trace` 日志自动生成或优化 Skill 描述。
- **环境自愈**: Frontmatter 中声明 `install` 策略（brew, uv, node 等），系统尝试自动修复缺失的依赖。

### 2.3 热重载 (Hot Reload)

- **配置重载**: 使用 `chokidar` 监听配置文件，动态更新 Gateway 运行时状态。
- **Skills 刷新**: 监听 Skills 目录变更，通过防抖机制批量同步至远程节点。

## 3. 避雷项：Vibe Coding 的代价

OpenClaw 宣称欢迎 "AI/vibe-coded PRs"，这导致其代码库存在严重的工程质量问题：

### 3.1 安全性极差 (Critical)

- **裸奔执行**: 默认在宿主环境执行所有工具，缺乏细粒度的权限隔离。
- **认证碎片化**: 权限检查逻辑散落在各个 `server-methods` 中，极易被绕过。
- **路径穿越**: 对工作空间路径的处理缺乏统一的校验层。

### 3.2 逻辑冗余与混乱

- **功能重叠**: `agent.ts` 与 `chat.ts` 之间存在大量重复的会话管理代码。
- **类型系统失效**: 过度使用 `any` 和不安全的类型断言，TypeScript 的保护作用微乎其微。
- **状态不可预测**: 错误处理逻辑不一致，部分模块静默失败，部分模块崩溃。

## 4. 对 Mental-Sync-CLI 的启示

- **采纳**: 借鉴其日志分析思路和基于监听器的热重载机制。
- **摒弃**: 坚决反对其不安全的执行模型。MSC 必须坚持 **Security by Design**，默认使用容器隔离。
- **优化**: 统一工具调用协议，避免 OpenClaw 式的功能模块碎片化。

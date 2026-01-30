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

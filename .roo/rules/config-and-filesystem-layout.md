# MSC Configuration & Filesystem Layout

> "Structure is the skeleton of intelligence; hierarchy is the map of sovereignty."

MSC v3.0 采用双层配置架构：**全局 (Global)** 负责身份与基础设施，**项目 (Project)** 负责任务上下文与局部规则。

## 1. 目录结构概览

### 1.1 全局配置 (Global)

路径: `$HOME/.msc/` (Windows: `%USERPROFILE%\.msc\`)

```text
.msc/
├── config.yaml          # 全局核心配置 (Provider, PFMS 路由, 默认偏好)
├── mcp.json             # 标准 MCP 服务器配置
├── modes/               # 自定义模式定义 (System Prompt 预设)
│   ├── architect.md     # 架构师模式定义
│   └── code.md          # 代码模式定义
├── knowledge-cards/     # 全局知识卡片库 (Lite RAG 检索，由Organizer负责填充和创建)
│   ├── python-best-practices.md
│   └── security-checklists.md
└── notebook/            # 全局 Notebook (跨项目长期记忆)
    └── memory-1.md
```

### 1.2 项目配置 (Project)

路径: `{workspace_root}/.msc/` 或兼容前缀

```text
.msc/ (或 .agent/, .roo/, .cline/ 等)
├── rules/               # 项目特定规则 (.md)
├── skills/              # 项目特定技能 (符合 Anthropic 动态上下文规范)
├── knowledge-cards/     # 项目特定知识卡片 (由 Organizer 蒸馏产生)
└── notebook/            # 项目 Notebook (当前任务状态与决策)
    └── memory-1.md
```

## 2. 配置文件规范

### 2.1 `config.yaml` (Global)

```yaml
version: "3.0"
default_mode: "architect"
pfms:
  providers:
    - name: "official-anthropic"
      type: "anthropic"
      api_key: "ENV:ANTHROPIC_API_KEY"
      # ... 详见 PFMS.md
```

### 2.2 模式定义 (`modes/*.md`)

模式文件采用 Markdown 格式，其完整内容作为该模式的 `Base System Prompt`。

## 3. 兼容性与加载优先级

MSC 遵循“就近原则”与“多框架兼容”策略。加载顺序如下：

1. **项目级规则 (Project Rules)**:
   - `.msc/rules/*.md` (最高优先级)
   - `.agent/rules/*.md`
   - `.roo/rules/*.md`
   - `.cline/rules/*.md`
   - `.cursor/rules/*.md`
   - `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`

2. **项目级技能 (Project Skills)**:
   - `.msc/skills/*.md`
   - `.agent/skills/*.md`
   - `.claude/skills/*.md`

3. **全局配置 (Global Config)**:
   - `$HOME/.msc/` 下的所有定义。

## 4. Anamnesis 实体承载

- **Notebook**: 存储在 `notebook/` 目录下。Main Agent 拥有读写权限，Sub-agent 默认只读或接收副本。
- **Knowledge Cards**: 存储在 `knowledge-cards/` 目录下。由 `Organizer` 写入，由 `Anamnesis` 通过 `Ltie RAG` 检索并注入上下文。

## 5. 开发者备注

- 可以将 API Key 存储在全局 `config.yaml` 中。全局配置目录 `$HOME/.msc/` 仅对 `green-tea` 开放访问权限。
- 所有路径引用应相对于当前工作区根目录或全局配置根目录。

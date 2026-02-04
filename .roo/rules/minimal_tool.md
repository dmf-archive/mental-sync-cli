# MSC Minimal Tool Set

> "在敌对环境中最小化攻击面，在自由能约束下最大化表达能力。"

## 核心原则

1. **系统工具优先**: 优先使用系统原生命令行工具（`cat`, `grep`, `ast-grep` 等），通过 `execute` 统一调度。
2. **必要才封装**: 仅当系统工具无法保证原子性、结构化输出或安全性时，才提供内置工具。
3. **路径白名单**: 所有文件访问默认拒绝，通过 `sandbox_config.allowed_paths` 显式授权。

## 最小工具集 (v1.0)

| 工具 | 类型 | 必要性 | 理由 |
| :--- | :--- | :--- | :--- |
| `write_file` | 内置 | **核心** | 原子写入 + 自动备份；系统 `echo` 无法保证完整性，无法支持存档点回溯能力 |
| `apply_diff` | 内置 | **核心** | 外科手术式修改；精确编辑代码的必备武器 |
| `list_files` | 内置 | **核心** | 结构化 JSON 输出；系统 `ls` 格式冗余难以解析 |
| `execute` | 内置 | **核心** | 一切系统工具的入口；通过提示词动态发现可用 CLI 工具 |
| `model_switch` | 内置 | **核心** | PFMS 路由入口，Main Agent自我插拔 |
| `create_subagent` | 内置 | **核心** | PFMS 路由入口；连接 Main Agent 与 Sub-agent 生态 |
| `memory_add` | 内置 | **核心** | Anamnesis 声明式接口；Agent 自我记忆的 CRUD |
| `memory_replace` | 内置 | **核心** | 同上 |
| `memory_del` | 内置 | **核心** | 同上 |

## 明确排除的工具

| 工具 | 排除理由 |
| :--- | :--- |
| `read_file` | 系统 `cat` 足够；通过 `execute` 调用即可 |
| `grep` | 系统 `grep`/`rg` 足够；通过 `execute` 调用即可 |
| `ast_grep` | 系统安装 `ast-grep` 足够；通过 `execute` 调用即可 |
| `fetch_url` | 使用系统 `curl`/`wget`；通过prompt提示和 `execute` 调用即可 |

## 安全模型

### 路径白名单 (Path Whitelist)

通过交互式TUI弹窗等更新，也可以直接编辑配置文件。

```yaml
sandbox_config:
  allowed_read_paths:
    - "./src"
    - "./tests"
  allowed_write_paths:
    - "./src"
  sensitive_paths:  # 即使白名单也需强制 HIL
    - "**/.env*"
    - "**/.ssh/"
    - "**/secrets.*"
    - "**/token.*"
```

### 权限分级

| 等级 | 描述 | 触发条件 |
| :--- | :--- | :--- |
| `auto` | 自动执行 | 路径在白名单内，非敏感路径 |
| `hil` | 人工审批 | 路径不在白名单，或命中敏感路径模式 |
| `deny` | 拒绝执行 | 路径在黑名单（如 `/etc/passwd`） |

## 工具 Schema 规范

所有内置工具遵循 MCP-like JSON Schema 定义，通过 `msc.core.tools` 统一注册。

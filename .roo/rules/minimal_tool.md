# MSC Minimal Tool Set

## 核心原则

1. **系统工具优先**: 优先使用系统原生命令行工具（`cat`, `grep`, `ast-grep` 等），通过 `execute` 统一调度。
2. **必要才封装**: 仅当系统工具无法保证原子性、结构化输出或安全性时，才提供内置工具。
3. **路径白名单**: 所有文件访问默认拒绝，通过 `sandbox_config.allowed_paths` 显式授权。

## 最小工具集 (v1.0)

| 工具 | 类型 | 理由 |
| :--- | :--- | :--- |
| `write_file(path(str);content(str))` | 内置 | 原子写入 + 自动备份；系统 `echo` 无法保证完整性，无法支持存档点回溯能力 |
| `apply_diff(path(str);diff(str))` | 内置 | 外科手术式修改；精确编辑代码的必备武器 |
| `list_files(path(str);recursive(bool))` | 内置 | 结构化 JSON 输出；系统 `ls` 格式冗余难以解析 |
| `execute(command(str);cwd(str))` | 内置 | 系统默认shell的入口；通过提示词动态更新可用 CLI 工具 |
| `model_switch(model_name(str))` | 内置 | PFMS 路由入口，Main Agent自我插拔 |
| `create_agent(task_description(str);model_name(str);require_caps(list);require_thinking(bool);shared_memory(bool);sandbox_config(dict))` | 内置 | PFMS 路由入口；连接 Main Agent 与 subagent 生态 |
| `ask_agent(agent_id(str);message(str);priority(str))` | 内置 | 跨代理通信接口；支持 standard/high 优先级消息传递。`agent_id=0` 指向 Main Agent。 |
| `memory(action(str);message(str);key(str))` | 内置 | Anamnesis 声明式接口；Agent 自我记忆的 CRUD |

## 明确排除的工具

| 工具 | 排除理由 |
| :--- | :--- |
| `read_file` | 通过 `execute` 调用系统 `cat`|
| `grep` | 通过 `execute` 调用系统 `grep`/`rg`|
| `ast_grep` | 通过 `execute` 安装 `ast-grep` 即可 |
| `fetch_url` | MCP server for search and fetch |

## 安全模型

### 路径和命令行前缀白名单 (Path Whitelist)

通过交互式TUI弹窗等更新，也可以直接编辑配置文件。

```yaml
sandbox_config:
  # 标准策略：适用于大多数 subagent
  normal:
    allowed_read_paths:
      - "./src"
      - "./tests"
    allowed_write_paths:
      - "./src"
    deny_read_paths:
      - ".env"
      - "**/*.key"
    deny_write_paths:
      - "pyproject.toml"
    allowed_exec_command:
      - "pnpm"
      - "pytest"
      - "ruff"
      - "mypy"
      - "uv sync"
    deny_exec_command:
      - "git rm"
      - "rm -rf *"

  # 绿茶策略：仅适用于具备 green-tea 标签的受信任 Provider
  # 可以额外补充但自动继承 normal 的 allowed 配置，但拥有独立的 deny 配置
  green_tea:
    inherit: "normal"
    allowed_read_paths:
      - "$HOME/.msc"  # 自动授权访问全局配置
    deny_read_paths: [] # 绿茶模式下允许读取敏感配置进行管理
    allowed_exec_command:
      - "git"
      - "curl"
```

### 权限分级

| 等级 | 描述 | 触发条件 |
| :--- | :--- | :--- |
| `pass` | 自动执行 | 路径在白名单内|
| `check` | 人工审批 | 路径不在白名单 |
| `deny` | 拒绝执行 | 路径在黑名单 |

### IPC 协议规范

当通过 `ask_agent` 进行结构化通信时，`message` 字段应包含以下 JSON 格式以触发特定逻辑：

### 1. 审批请求 (Approval Request)

用于 subagent 向父级或 Main Agent 申请高危操作权限。

```json
{
  "type": "approval_request",
  "action": "execute",
  "params": { "command": "rm -rf ./tmp" },
  "reason": "Cleanup temporary build artifacts"
}
```

### 2. 任务结果回传 (Task Result)

subagent 完成任务后，必须向 `agent_id=0` 发送此格式。

```json
{
  "type": "task_result",
  "status": "success",
  "data": { "summary": "Analysis complete", "files_generated": ["report.md"] }
}
```

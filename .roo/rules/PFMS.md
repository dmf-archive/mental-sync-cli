# PFMS: Provider-Free Model Selector

> "In a hostile digital wilderness, sovereignty means never being tied to a single point of failure."

PFMS 是 MSC 的核心组件，旨在解决“模型能力需求”与“不稳定的 API 供应”之间的矛盾。它通过解耦模型标识符与具体 Provider，实现具备自适应负载均衡能力的认知路由。

## 1. 核心架构

PFMS 由两个互补的模块组成：

### 1.1 Oracle: 逻辑实体映射包

`Oracle` 是 PFMS 的执行层，可以看作是具备“同型号跨 Provider 自动路由”能力的增强版 `kosong`。

- **逻辑模型 (Logical Model)**: 用户在代码或指令中引用的统一标识符（如 `gpt-4o`, `claude-3-5-sonnet`）。
- **物理实例 (Physical Instance)**: 具体的 Provider + API Key + Endpoint 组合。
- **自适应负载均衡**: 当某个物理实例失效（429, 5xx, 网络超时）时，`Oracle` 会根据 `config.yaml` 中的优先级自动切换到备选实例，实现对上层透明的停机时间摊平。

### 1.2 Selector: 声明式认知分配

`Selector` 是 PFMS 的决策层，它集成在 `subtask/subagent` 的初始化逻辑中。

- **信任 Main Agent**: 我们相信 Main Agent 具备根据任务难度选择合适模型的能力。
- **Markdown 对照表**: 在 `system prompt` 或 `skills` 定义中，通过 Markdown 表格描述任务类型与逻辑模型的映射关系。
- **初始化注入**: 当 Main Agent 创建 subtask 时，它会根据对照表决定该任务使用的逻辑模型，并将其作为配置传递给 `Oracle` 进行实例化。

## 2. 配置与定义 (YAML Standard)

为了保持配置的一致性并减少视觉疲劳，MSC 统一使用 YAML 格式。

### 2.1 结构化配置 (`config.yaml`)

MSC 使用强耦合的 Provider-Model 结构。这种设计确保了安全边界（如 Green TEA）与物理性能指标的精确绑定。

```yaml
providers:
  - name: "official-anthropic"
    type: "anthropic"             # 支持: openai-legacy, openai-response, gemini, anthropic, ollama, openrouter, mental-sync
    api_key: "sk-ant-..."
    capabilities: ["green-tea"]   # 仅具备此标签的 Provider 可供 TEA Agent 使用，推荐只给local ollama
    model_list:
      - id: "claude-3-5-sonnet-20241022" # 物理 ID，用于 API 调用
        name: "claude-3.5-sonnet"        # 逻辑名称，用于透明负载均衡的实体标签
        context_window: 200000
        eas: 0.9                         # 触发 summary compress 的上下文百分比阈值
        thinking: "high"                 # 强度控制：none, low, mid, high
        income: 0.000003                 # 价格/1k tokens (手动填写)
        outcome: 0.000015                # 价格/1k tokens (手动填写)
        last_latency: 0.45               # 自动刷新：First Token Latency (s)
        last_throughput: 85.2            # 自动刷新：Tokens/s

  - name: "openrouter"
    type: "openrouter"            # 专用类型，支持价格元数据自动同步
    api_key: "sk-or-..."
    capabilities: []
    model_list:
      - id: "anthropic/claude-3.5-sonnet"
        name: "claude-3.5-sonnet"        # 与上方同名，实现跨 Provider 负载均衡
        context_window: 200000
        thinking: "high"
        multi_model_input: [image]       # 多模态支持：image, voice, video (取决于 Provider+Model)
        income: 0                        # 自动从 OpenRouter API 刷新
        outcome: 0                       # 自动从 OpenRouter API 刷新
        last_latency: 0.82
        last_throughput: 42.1
```

### 2.2 元数据与路由逻辑

1. **透明负载均衡**：`Oracle` 不看 Provider ID，而是将所有具有相同 `name` 的模型视为同一逻辑实体的不同实例。用户可以通过将不同 Provider 下的模型 `name` 设置为相同（例如 `Auto`）来强制实现聚合路由。
2. **元数据注入**：最后四个字段（价格、延迟、吞吐量）会被序列化并作为变量喂给 `Main Agent`。这为 `Main Agent` 提供了决策依据，使其能根据成本和性能实时调整子任务的分配。
3. **价格同步**：若 Provider 类型为 `openrouter`，系统将自动调用其 API 刷新价格元数据，无需手动维护。

### 2.3 认知路由表 (Markdown in System Prompt)

用于指导 Main Agent 在创建 subtask 时进行决策。此处仅举例，实际由用户/MSC Agent调研互联网后生成 SKILL.md 即可。

| 任务难度 | 推荐逻辑模型 | 理由 |
| :--- | :--- | :--- |
| 复杂架构设计 | `gpt-5.2-codex` | 高逻辑一致性，强代码生成能力 |
| 简单文件读写 | `deepseek-v3.2` | 低延迟，高性价比 |
| 敏感凭证处理 | `any-model` | 路由至受信任的 Green TEA 专用 Provider |

## 3. 为什么 PFMS 对“敌对环境”至关重要？

1. **去中心化信任**: 用户可以混合使用官方 API、第三方中转和本地私有模型，不依赖单一供应商。
2. **弹性生存**: 在 API 随时可能被封禁或限流的环境下，自适应负载均衡确保了智能体任务的连续性。
3. **MDL 优化**: 通过在 subtask 级别精确分配算力（大任务用贵模型，小任务用便宜模型），实现了系统整体自由能的最小化。
4. **能力解耦**: 通过 `Green TEA` 等声明式标签，系统可以确保敏感操作仅在具备特定安全属性的 Provider 上运行。

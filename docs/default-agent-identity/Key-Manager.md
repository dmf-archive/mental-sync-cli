# Key-Manager: Provider-Free API 聚合与安全架构

> "The main brain dreams of APIs; the shadow hand signs the checks."

## 1. 背景与问题

为了实现 Agent 的高度自举（Self-bootstrapping），我们需要赋予它自主获取资源的能力——包括自主搜索、订阅甚至付费使用第三方 API。然而，这带来了巨大的安全风险：

- **数据泄露**: 如果主模型直接接触 API Key，这些密钥会泄露给模型提供商。
- **权限滥用**: Agent 会在无意中消耗过多的额度。

为此，我们引入 **Key-Manager** 架构，实现逻辑推理与凭证管理的物理隔离。

## 2. 核心架构

### 2.1 角色分工

1. **Main Agent (主智能体)**:
   - **职责**: 规划任务、编写代码、调用工具、搜索互联网。
   - **视野**: **只能看到环境变量名** (e.g., `${SEARCH_API_KEY}`)，**绝对无法**接触明文密钥。
   - **能力**: 可以通过操作变量名来“配置”工具。例如，它可以决定使用 `${NEW_API_KEY}`，但它不知道这个 Key 的具体内容。

2. **Key-Manager (安全/凭证智能体)**:
   - **职责**: 专门负责处理认证、支付表单填写、密钥注入。
   - **视野**: 可以接触明文密钥、支付凭证等敏感信息。
   - **限制**: **必须**运行在受信任的执行环境中（Local Execution Environment）。
   - **模型要求**: 必须连接到人类手动标记为 `SAFE` 的 API 端点（例如本地运行的 Ollama）。严禁连接公有云模型。

### 2.2 Provider-Free API Aggregation

我们构建一个中间层，使得 Main Agent 认为它在使用一个通用的、无需特定 Provider 的 API 网关。

- **Discovery (发现)**: Main Agent 可以在互联网上搜刮 API 文档。
- **Negotiation (协商)**: Main Agent 生成一个“订阅请求”，包含所需的 API 类型和预算。
- **Fulfillment (履约)**:
  1. 系统暂停 Main Agent。
  2. 唤醒 Key-Manager。
  3. Key-Manager 读取“订阅请求”，在本地安全环境中访问用户的“凭证库”（Credential Vault）。
  4. Key-Manager 登录目标网站，获取 API Key，或从凭证库中提取现有 Key。
  5. Key-Manager 将 Key 写入系统的环境变量存储（`.env` 或加密存储），并返回一个**变量名**给系统。
  6. 系统恢复 Main Agent，并告知：“API 已就绪，请使用环境变量 `${GENERATED_API_KEY_001}` 调用。”

## 3. 安全协议 (Security Protocol)

1. **隔离原则**: Main Agent 的 Context Window 中永远不应出现以 `sk-` 开头的字符串或高熵随机符。
2. **人类审计**: Key-Manager 的所有资金相关操作（如“点击付费按钮”）必须经过 TUI 的显式人类审批（Human-in-the-loop）。
3. **自我充电**: 在极端自举场景下，如果 Agent 需要更多算力，Main Agent 提出请求，Key-Manager 负责在预算范围内去云服务商处“充值”或“开通新实例”，全程密钥不离本地。

## 4. 总结

Key-Manager 是 `Mental-Sync-CLI` 的“财务总监”与“安全官”。它确保了即便主大脑（Main Agent）被入侵或不可信，核心资产（密钥与资金）依然由本地的、受限的小模型严密看管。

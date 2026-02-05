# Action Plan: Native Tool Call Support & Capability Detection

> "Trust but verify; detect before you delegate."

## 1. 核心目标

在 MSC 面对环境不可信场景时，解析器必须具备“能力感知”能力。我们需要在 Oracle 配置文件中增加 `tool` 标签，并确保 `ToolParser` 能够根据模型能力动态切换解析策略。

## 2. 架构变更

### 2.1 Oracle 能力模型扩展

在 `msc/oracle/__init__.py` 和各适配器中，增加 `has_tools` 属性。

- **has_tools**: 布尔值，表示模型是否支持原生的 Function Calling 接口。
- **require_caps**: 在 `Oracle.generate` 中增加对 `tool` 标签的显式要求。

### 2.2 动态解析策略 (Hybrid Parsing)

`ToolParser` 将演进为混合模式：

1.  **Native Mode**: 如果模型 `has_tools=True`，优先使用 Provider 返回的结构化 `tool_calls` 字段。
2.  **Regex/Block Mode**: 如果模型不支持原生工具调用，或者作为 Native Mode 的 Fallback，使用增强的“平衡括号”或“代码块提取”算法解析文本。

## 3. 配置文件修订 (`.roo/rules/PFMS.md`)

已在 `PFMS.md` 中增加了 `multi_model_input: [image, tool]` 标签，用于标识原生工具调用支持。

## 4. 实施步骤

1.  [x] **修订文档**: 更新 `PFMS.md` 以反映新的能力标签。
2.  [x] **接口定义**: 在 `ModelCapability` 协议中增加 `has_tools`。
3.  [x] **适配器更新**: 在 `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter` 中实现 `has_tools` 逻辑。
4.  [ ] **OG 逻辑增强**: 在 `Session.run_loop` 中根据模型能力决定是否传递工具定义，并优先处理结构化返回。
5.  [ ] **ToolParser 重构**: 引入更稳健的块提取逻辑，彻底解决嵌套 JSON 问题。

## 5. 验证计划 (TDD)

- **Case 1**: 使用具备 `tool` 能力的模型，验证 `Oracle` 是否透传了结构化工具调用。
- **Case 2**: 使用不具备 `tool` 能力的模型，验证 `ToolParser` 是否能从文本中稳健提取 JSON。
- **Case 3**: 验证路由逻辑是否正确拦截了不支持 `tool` 但被要求 `require_caps=['tool']` 的请求。

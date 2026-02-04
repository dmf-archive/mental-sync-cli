# Oracle 子包施工总结 (Final)

> **命名原由**: 在 Mental-Sync-CLI 执行框架中，大语言模型被视为提供决策与知识的“神谕”（Oracle）。本子包作为连接现实世界 API 与智能体认知的桥梁，负责路由、分发并确保这些神谕的可靠抵达。

> **TCB (Trusted Computing Base) 声明**:
>
> 1. **用户责任制**: 配置文件被视为 TCB 的一部分。系统信任配置文件的物理安全性。
> 2. **原子化管理**: 配置文件采用原子化管理方式，任何对敏感标签（如 `green-tea`）的误用由配置者承担。

## 1. 概述

`oracle` 已作为 PFMS (Provider-Free Model Selector) 的执行层完成开发。它实现了 Model/Provider Free 的核心愿景，支持同型号跨 Provider 自动路由、基于配置顺序的隐式优先级调度以及透明的故障转移。

## 2. 核心数据模型与协议

为了确保类型安全与运行时的灵活性，我们采用了 `typing.Protocol` 进行接口定义，并使用 `Pydantic` 进行配置校验。

```python
@runtime_checkable
class ModelCapability(Protocol):
    has_vision: bool
    has_thinking: bool

@runtime_checkable
class ChatProvider(Protocol):
    name: str
    model_name: str
    capabilities: List[str]
    model_info: ModelCapability
    async def generate(self, prompt: str, image: Optional[str] = None) -> str: ...
```

## 3. 架构设计

### 3.1 适配器模式 (Adapter Pattern)

我们实现了针对主流 LLM 供应商的深度适配，所有适配器均隐藏了底层 SDK 的复杂性：

- **OpenAIAdapter**: 封装 `openai.AsyncOpenAI`，支持所有 OpenAI 兼容端点（如 DeepSeek, Groq）。
- **AnthropicAdapter**: 封装 `anthropic.AsyncAnthropic`，支持原生 Messages API。
- **GeminiAdapter**: 封装 `google.genai.Client`，支持 VertexAI 与 Google AI Studio。
- **OllamaAdapter**: 继承自 `OpenAIAdapter`，专为本地推理优化，默认指向 `http://localhost:11434/v1`。
- **OpenRouterAdapter**: 继承自 `OpenAIAdapter`，支持通过公开端点**异步刷新价格**（$/1M tokens），且不带 API Key 以保护隐私。

### 3.2 路由与故障转移逻辑

- **隐式优先级**: `Oracle` 接收一个 Provider 列表，其物理顺序即代表了调用的优先级。
- **能力感知分发**: 路由时会自动匹配 `require_caps` (如 `green-tea`)、`has_vision` 和 `has_thinking` 标签。
- **透明重试**: 当首选实例返回异常（如 429, 5xx）时，系统会自动尝试列表中的下一个候选者，直到成功或尝试完所有可用实例。

## 4. 安全性设计

- **配置加载**: 在 `msc.oracle.config` 中，我们强制使用 `yaml.SafeLoader` 加载配置，从根源上杜绝了通过 YAML 反序列化触发的任意代码执行（ACE）风险。
- **隐私保护**: OpenRouter 的价格刷新机制采用匿名请求，不向公开端点泄露用户的 API Key。

## 5. 验证记录

- **单元测试**: 通过 [`tests/oracle/test_oracle.py`](../../tests/oracle/test_oracle.py) 验证了核心路由算法、能力过滤和安全加载逻辑。
- **集成测试**: 通过 [`tests/oracle/test_integration.py`](../../tests/oracle/test_integration.py) 在本地转发器（`http://localhost:8317`）上实地验证了 OpenAI、Anthropic 和 Gemini 三种异构格式的完全兼容性。

## 6. 结论

`oracle` 子包已具备生产级可靠性，成功屏蔽了底层供应商的差异，为 Mental-Sync-CLI 提供了坚实的认知路由基础。

---
name: model-select-advice
description: "Proactively invoke this skill when needing to select or update the optimal LLM models based on real-time pricing and performance data from OpenRouter, specifically focusing on the 'Core 7' elite models."
---

# Skill: model-select-advice

此技能旨在指导智能体通过 OpenRouter API 获取实时数据，并结合“Core 7”模型标准，为用户提供科学的模型选择建议。

## 1. 核心概念：什么是 Core 7？

由于此技能可能被不具备最新知识补丁的模型加载，在此明确 **Core 7** 的定义：
**Core 7** 指的是 2025 年至 2026 年初 AI 军备竞赛中处于第一梯队的七大模型家族/供应商。它们代表了当前计算能力的巅峰：

1. **OpenAI**: GPT-5.2 。
2. **Anthropic**: Claude 4.5 。
3. **Google**: Gemini 3 。
4. **DeepSeek**: V3.2 。
5. **Alibaba (Qwen)**: Qwen3 。
6. **Moonshot (Kimi)**: Kimi K2.5 。
7. **xAI (Grok)**: Grok 4.2 。

## 2. 自动化获取流程

### 2.1 获取最新列表与价格

优先使用 Python 脚本获取并格式化 OpenRouter 模型数据，以确保价格单位（每百万 Token）的准确性与输出的可读性。

```bash
python .roo/skills/model-select-advice/scripts/fetch_models.py
```

```powershell
python .roo/skills/model-select-advice/scripts/fetch_models.py
```

### 2.2 验证与搜索

在获取价格列表后，必须执行以下步骤：

1. **价格排序**: 识别当前最经济的 Core 7 实例。
2. **互联网验证**: 使用 `exa-code` 或 `web_search` 搜索 `[Model ID] user review 2026` 或 `[Model ID] benchmark vs [Competitor]`。
3. **用户确认**: 向用户展示对比表，并询问：“是否根据此优先级顺序生成/更新 PFMS 路由表并固化为 SKILL？”

## 3. 常见借口与现实 (Rationalization Table)

| 常见借口 (Rationalization) | 现实 (Reality) |
| :--- | :--- |
| “我可以直接根据记忆推荐模型，没必要查实时数据。” | **认知滞后是致命的**。2026 年的 API 市场波动剧烈，价格和性能指标每周都在变动。不查实时数据必然导致使用已过时的模型。 |
| “OpenRouter 的 API 响应太慢，为了效率我应该跳过这一步。” | **效率不能以牺牲准确性为代价**。宁可等待 5 秒获取真实价格，也不要让用户在不知情的情况下消耗高昂的 Token 成本。这是对用户资源的尊重。 |
| “Core 7 之外的模型可能在特定领域更好，我应该推荐它们。” | **警惕长尾陷阱**。在大模型竞赛中，Core 7 占据了绝对的算力和数据优势。除非有明确的 Benchmark 证据，否则推荐非 Core 7 模型通常是基于过时信息或直觉的误导。 |
| “我只需要看模型名称，Provider 之间的差异可以忽略。” | **Provider 决定了稳定性**。即使是同一个模型，不同 Provider 的延迟（TTFT）和吞吐量可能相差数倍。|

## 4. 红灯信号 (Red Flags)

- [ ] **盲目自信**: 在未执行 `fetch_models.py` 获取 OpenRouter 实时数据的情况下给出模型建议。
- [ ] **数据缺失**: 推荐模型时未能提供具体的 `$/1M tokens`（Input/Output）价格对比。
- [ ] **逻辑断层**: 推荐了不在 Core 7 列表内且未提供详细 Benchmark 或理由的模型。
- [ ] **静态思维**: 忽略了 OpenRouter 中同名模型不同 Provider 的延迟差异，未进行性能排序。
- [ ] **跳过验证**: 在未进行互联网搜索（如 `exa-code`）验证模型最新口碑的情况下声称其为“当前最强”。

## 5. 自举 (Self-Bootstrap)

当检测到 Core 7 家族发布新一代旗舰模型（如 GPT-6, Claude 5 等）时，执行以下自举步骤：

修改本文件第一节 `## 1. 核心概念` 中的模型代数，确保其反映最新的技术代际。

## 6. 参考资源

- 示范性手册: [`assets/recommendation_handbook.md`](.roo/skills/model-select-advice/assets/recommendation_handbook.md)
- 抓取脚本: [`scripts/fetch_models.ps1`](.roo/skills/model-select-advice/scripts/fetch_models.ps1)

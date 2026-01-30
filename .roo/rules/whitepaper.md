---
title: "Mental-Sync-CLI (MSC) 项目白皮书"
version: "1.0.0"
status: "Official"
author: "Chain://Research"
last_updated: "2026-01-29"
---

# Mental-Sync-CLI (MSC) 项目白皮书

> "在虚构的叙事中构建真实的工具，在敌对的环境中寻找逻辑的庇护。"

## 1. 项目愿景与定位

**Mental-Sync-CLI (MSC)** 是一个连接叙事与工程的脚手架。它既是 `Web://Reflect` 世界观下的 ARG (Alternate Reality Game) 道具，也是一个可信赖的、本地优先的、高度定制化的 **Code Agent 运行时环境**。

其核心目标是填补 `IPWT` (理论) / `Tiny-ONN` (模型) 与实际代码实现之间的真空，探索在资源受限且默认敌对的数字环境中，如何构建具备自举进化能力的智能体系统。

## 2. 核心设计哲学

- **叙事驱动工程 (Narrative-Driven Engineering)**: 将科幻设定（如 Agent Core, Anamnesis, OSPU）映射为具体的工程模块（如 Agent 逻辑、记忆管理、安全沙箱）。
- **最小描述长度 (MDL)**: 追求极致的代码压缩率和依赖精简，遵循自由能原理，降低系统熵。
- **设计安全 (Security by Design)**: 采用 "Zero-Trust" 架构，默认拦截所有高危操作，所有敏感行为需显式授权。
- **自举进化 (Self-Bootstrapping)**: 系统内置元认知循环（Reflect-Agent），通过分析执行日志实现自我诊断与优化。

## 3. 系统架构

MSC 采用分层架构，确保组件间的解耦与灵活性：

- **交互层 (Interface)**: 提供 TUI (Rich/Textual) 和 CLI (Typer) 界面，支持自然语言与 Shell 命令混合交互。
- **编排层 (Orchestration)**: 核心为 `Wire Protocol` 通信总线，负责组件间的异步消息传递与权限审计。
- **认知层 (Cognition)**: 包含 `Agent Core` (决策核心)、`Skills` (技能注册表) 和 `Anamnesis` (上下文与记忆管理)。
- **基础设施层 (Infrastructure)**: 提供多平台沙箱隔离（Landlock/Restricted Token）、凭证管理（Key-Manager）及向量知识库。

## 4. 关键技术决策

- **语言栈**: Python 3.13+，利用最新的类型系统和性能特性。
- **依赖管理**: 强制使用 `uv`，确保构建速度与环境一致性。
- **安全模型**: 默认拒绝 (Default Deny) 策略，关键操作需通过 `ApprovalRequest` 进行人工审批。
- **编码规范**: 严格类型安全，代码自解释（禁止冗余注释），确保 Agent 生成代码的高质量。

## 5. 现实版 PoPI (预测完整性证明)

我们将故事中的 PoPI 转化为工程质量指标：
1. **语法有效性**: 通过 `ruff` 和 `mypy` 校验。
2. **功能正确性**: 通过 `pytest` 单元测试。
3. **操作员满意度**: 最终的 Ground Truth，若人类无需干预即可完成任务，则视为 PoPI 成功。

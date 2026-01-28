---
title: "Mental-Sync-CLI (MSC) 开题报告"
version: "1.0.0"
last_updated: "2026-01-28"
status: "Draft"
author: "Chain://Research"
---

# Mental-Sync-CLI (MSC) 开题报告

> "在虚构的叙事中构建真实的工具，在敌对的环境中寻找逻辑的庇护。"

## 1. 项目背景与动机

### 1.1 IRES 的遗产与教训

本项目是 `IRES framework` (Independent Runaway Entity System) 的精神续作。

- **历史教训**: 早期的 IRES 实验因当时的基础模型 (Gemini 2.5 pro) 缺乏稳定且遵循指令的 JSON Function Calling 能力，导致 Agent 无法可靠地执行复杂任务链，最终沦为“扶不起的阿斗”。
- **技术转折**: 随着 Gemini 3、Claude 4.5 Sonnet 等模型在 Tool Use 和推理能力上的质变，构建一个真正自主、可靠的 Code Agent 已成为可能。

### 1.2 现有方案的局限性 (The Gap)

尽管市面上已有 `Codex` (OpenAI) 和 `Kimi Code` (Moonshot) 等优秀的 Code Agent，但它们无法完全满足 `Chain://Research` 的特殊生态位要求：

1. **低资源 (MDL)**: 遵循自由能原理和整合预测工作空间理论的指导，框架自身也应该是高效的。
2. **高效率 (High Efficiency)**: 一流的多代理集群工作流支持。
3. **零信任社会学 (Zero-Trust Sociology)**: `Chain://Research` 设定在一个默认敌对的数字环境中。我们需要更细粒度的权限控制、更透明的上下文审计，以及符合“逻辑根信任”的安全沙箱。现有的商业 Agent 往往过于“乐观”，缺乏对环境的防御性设计。

## 2. 项目定义：双重身分

MSC 本质上是一个**连接叙事与工程的脚手架**。它是一个“薛定谔的工具”，同时存在于两个层面：

### 2.1 叙事层 (The ARG Prop)

- **身份**: `Web://Reflect` 世界的 ARG 道具。方便作者玩 MSC meme.

### 2.2 工程层 (The Practical Tool)

- **身份**: 一个可信赖的、本地优先的、高度定制化的 Code Agent 运行时。

- **目标**: 填补 `IPWT` (理论) / `Tiny-ONN` (模型) 与实际代码实现之间的巨大真空。作者需要一个趁手的 Code Agent 而不只是 Roo code 或其他市售 Code Agent。

## 3. 核心架构规划

### 3.1 设计原则

1. **Scaffold First (脚手架优先)**: 优先解决“怎么运行 Agent”、“怎么控制权限”、“怎么管理上下文”的问题，而不是纠结于“Agent 有多聪明”。聪明是模型的事，可靠是脚手架的事。
2. **Protocol Agnostic (协议无关)**: 全面兼容 **MCP (Model Context Protocol)**, ACP（Agent Communication Protocol），和Provider-Free设计，确保工具生态的通用性，不重复造轮子。
3. **Security by Design (设计安全)**: 默认拦截所有高危操作（文件写入、网络请求），需用户显式授权（如gammy telegrambot等通讯方式）。

### 3.2 关键模块参考

- **Shell/TUI**: 深度参考 `ref/codex` 的 `ratatui` 实现，打造高性能、低延迟的终端界面。
- **Orchestrator**: 借鉴 `ref/kimi-cli` 的 `kosong` 抽象层，设计灵活的 Agent 编排机制，支持多模型切换。
- **Sandboxing**: 利用 Docker 或 OS 原生隔离机制（如 Linux Namespaces / Windows Sandbox），构建“数字防爆盾”。

## 4. 预期产出

1. **`msc` CLI**: 一个开箱即用的终端工具，支持自然语言指令与 Shell 命令的混合交互。
2. **预制prompt和skills**: 一套完整的 Agent 行为准则，指导 Agent 在 MSC 环境下如何高效、安全地工作。
3. **Unified Console**: 作为 `Chain://Research` 各个子项目 (Tiny-ONN, ARS, OSPU) 的统一控制台和实验启动器。

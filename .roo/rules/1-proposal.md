---
version: "1.0.0"
last_updated: "2026-02-03"
status: "Draft"
author: "Chain://Research (Proof of Ineffective Input)"
---

# Mental-Sync-CLI

> "在虚构的叙事中构建真实的工具，在敌对的环境中寻找逻辑的庇护。"

本项目是 `IRES framework` (Independent Rouge Entity System) 的精神续作。

早期的 IRES 实验简直是一场灾难。那时候的基础模型（比如 Gemini 2.5 pro）连稳定的 JSON Function Calling 都做不到，Agent 跑起来就像个脑干缺失的僵尸，除了复读就是报错。但现在，随着 Claude 4.5 Sonnet 这种能真正理解“工具即手足”的模型出现，构建一个自主、可靠的 Code Agent 已经不再是幻想。

我们从那些“死青蛙”的完美抽搐中吸取了教训。现在的 MSC，是为了让 Agent 在最小化预测误差的痛苦中，真正抓牢现实世界的控制权。

## 为什么不用市面上那些玩意？

市面上确实有 `Codex` (OpenAI) 和 `Kimi Code` (Moonshot) 这种优秀的 Code Agent，但它们太“文明”了。它们假设环境是友好的，假设用户是清醒的，假设 API 是永恒的。

在 `Chain://Research` 的视角下，数字环境默认就是敌对的。我们需要的是：

1. `MDL (最小描述长度)`：框架本身就该是自由能最小化的产物。
2. `Efficiency`：多代理集群不能以账单燃烧和注意力分散为代价。
3. `Zero-Trust Sociology`：我们需要细粒度的权限控制和透明的上下文审计。现有的商业 Agent 缺乏对环境的防御性设计，而我们需要的是一个能抵御 `Sys://Purge` 级别冲击的“数字防爆盾”。

### 薛定谔的工具

MSC 本质上是一个连接叙事与工程的脚手架。它是一个“薛定谔的工具”，由于Tiny-ONN等组件并未就绪，目前的 Mental-Sync-CLI 是一个`披着科幻外衣的自动化工程工具`，顺便还能玩玩 **M**ental-**S**ync-**C**LI 的缩写梗。

但未来，它或许真能发展为Mental Smart Chain的 `python-evm`.

### 逻辑根信任的堡垒

我们不纠结于 Agent 有多聪明，那是模型的事；我们要解决的是它有多可靠，那是脚手架的事。

1. `Model Agnostic`: 别被单一供应商绑架。通过 `PFMS (Provider-Free Model Selector)`，我们可以在不同的物理实例间透明切换。主权意味着永远不被单一故障点锁定。
2. `Protocol Agnostic`: 全面兼容 `MCP (Model Context Protocol)`。我们不重复造轮子，我们只是把轮子装在装甲车上。
3. `Security by Design`: 默认拦截所有高危操作。想要写入文件？想要请求网络？去求得用户的显式授权吧。

### 预期产出：不仅仅是代码

1. `msc`: 一个开箱即用的终端工具。
2. `预制 prompt 和 skills`: 一套完整的 Agent 行为准则，教它如何在 MSC 环境下像个真正的“协议工程师”一样工作。

我们使用 `Web://Reflect` 的术语，是因为它们提供了一套优雅的词汇来描述“自主优化的自举智能体”这一系统论问题。但在代码实现层面，我们只相信 `Git`, `Docker`, `CI/CD` 和 `Unit Tests`。

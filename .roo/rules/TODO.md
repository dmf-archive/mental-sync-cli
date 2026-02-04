# MSC Bugs & TODOs

- [x] `msc/core/anamnesis/metadata.py`: `MetadataProvider.collect` 中 `active_terminals`, `resource_limits`, `capabilities` 已初步实现（支持 Windows 进程检查和基础资源统计）。
- [-] `msc/core/tools/agent_ops.py`: `CreateAgentTool.execute` 中 PFMS 路由逻辑仍为占位符，仅返回随机 ID。
- [x] `msc/oracle/adapters/anthropic.py`: `AnthropicAdapter.generate` 已实现基础的 Base64 图像处理逻辑。
- [x] `msc/oracle/adapters/gemini.py`: `GeminiAdapter.generate` 已实现基础的 Base64 图像处理逻辑。

## 待办事项 (New)

- [ ] `msc/core/tools/agent_ops.py`: 实现真正的 subagent 进程派生与 PFMS 路由验证。
- [ ] `msc/core/anamnesis/metadata.py`: 增强 `active_terminals` 在 Linux/macOS 下的兼容性。
- [ ] `msc/oracle/adapters/anthropic.py`: 增加对多图输入的支持。

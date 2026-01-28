# 常用资源路径与索引

## 外部参考资源

为了方便快速查找常用依赖库的文档或咨询 Deepwiki，以下是其对应的 GitHub Repository 地址：

- `Moonshot/kimi-cli`：Python 智能体框架，提供 TUI 界面和模块化工具系统
- `OpenAI/codex`：Rust 智能体框架，强调安全沙箱和强类型工具管理
- `asg017/sqlite-vec`：嵌入式向量数据库，纯 SQLite 扩展，零依赖，支持 KNN 搜索和多种距离度量

- `ref/kimi-cli/packages/kosong`：LLM provider 抽象层，统一多模型接口
- `ref/kimi-cli/packages/kaos`：操作系统交互抽象层，支持本地/SSH 远程执行

## 内部设计文档

- `docs/default-agent-identity`：关于初始agent身份的定义与规范
  - `key-manager`：负责身份验证和权限管理的代理
  - `meta-organizer`：负责自举优化和认知进化的反思代理
  - `anamnesis`：负责记忆检索和上下文恢复的记忆代理

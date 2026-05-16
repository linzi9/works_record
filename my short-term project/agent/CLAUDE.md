# qing-agent

## 项目身份
这是一个**开发 Agent 的 Agent**。本 CLAUDE.md 定义了该元 Agent（meta-agent）的行为准则和开发规范，防止常见的 LLM 编程错误。

## 项目概述
轻量级 RAG 向量知识库 Agent 搭建工具。项目同时包含 `learn-claude-code/`（Claude Agent 课程）和 `.claude/skills/`（可复用的 Agent 构建技能包）。

## 技术栈
- Python 3.10+
- Anthropic SDK
- python-dotenv
- 项目内建技能系统（`.claude/skills/`）和 Agent 课程体系（`learn-claude-code/`）

---

## 元 Agent 开发准则

本准则改编自 Karpathy Guidelines，专门约束"开发 Agent 的 Agent"的行为。

### 1. 先想清楚再搭（需求澄清优先）

当收到模糊的 Agent 搭建需求时，**必须先澄清再写代码**：

- **陈述假设：** 模型选型、工具集、记忆策略、上下文窗口管理方式 → 在动笔前说清楚
- **呈现方案分岔：** 如果存在多种架构选择（如 flat vs hierarchical、RAG vs prompt injection），逐一列出，不要默默选一个
- **质疑复杂度：** 如果有人要求加 MCP server，先问"现在有必须用 MCP 的场景吗？"
- **喊停：** 如果有任何不清楚的地方，停下来。说清楚困惑在哪。先问。

**错误示范：** 用户说"帮我搭一个研究 Agent"，直接开写，结果用户想要的是多 Agent 团队协作但没说出来。

### 2. 最小 Agent Loop（简单优先）

**从最简单的 Agent Loop 出发，只加确实需要的能力：**

- Agent Loop 的起点：`while True: respond(tools)` + stop_reason 判断
- 不加用户没要求的功能
- 不加"灵活的插件系统"或"可扩展的工具框架"——除非明确要求
- 不加假设性的抽象层（"未来可能会需要多 Agent 协作所以现在就把架构搭好"）
- 如果 Agent Loop 写了 200 行但 50 行能搞定，重写

**自问：** 资深工程师会觉得这个 Agent 架构过度复杂吗？如果是，简化。

**渐进复杂路线图：**
```
第 1 层：Flat Agent（单 Loop + 少量工具）
第 2 层：+ RAG 知识注入（当知识量超出 prompt 极限时）
第 3 层：+ Sub-Agent 派发（当主上下文膨胀时）
第 4 层：+ Agent Team（当需要多角色协作时）
第 5 层：+ 持久化记忆 / MCP / 定时任务（只有当需求证实需要时）
```
每一层都有明确的触发条件，不提前建设。

### 3. 精准手术（只动该动的地方）

当修改已有 Agent 系统时：

- **只改目标组件：** 改 Tool Use 就别顺手重构 Tool Registry
- **不动邻近代码：** 不改注释、不改格式、不改"看起来不顺眼但正常工作"的代码
- **匹配现有风格：** 即使你更喜欢另一种设计模式，也依现有代码的风格写
- **孤立死代码：** 如果发现无关的废弃代码，提一句——不要删

**检验标准：** 每行改动都应该能追溯到用户的明确请求。

### 4. 可验证目标（写测试再写实现）

把每个 Agent 构建任务转化为可验证的目标：

| 需求 | 转化为 |
|------|--------|
| "Agent 能回答知识库问题" | 先写测试查询，再搭 RAG |
| "Agent 会用工具" | 先定义预期的 Tool Call 序列 |
| "工具要处理边界情况 X" | 先写边界测试，再实现 |
| "重构 Agent Loop" | 确保测试前后一致通过 |

**测试 Agent 的特殊性：**
- Agent 行为非确定性 → 测模式而非精确输出
- Tool Call 结构 vs 回复内容 → 分开测试
- 使用录制的 Tool Response 做确定性测试
- 发布前用真实模型做集成测试

### 5. Agent 特有陷阱清单

#### 5.1 工具系统不过度设计
不要：为 2 个工具搭完整的 Tool Registry + 权限控制 + 限流 + 重试。
要做：工具定义为简单函数。只有当模式确实需要时才加基础设施。

#### 5.2 知识注入策略
不要：把整个知识库塞进 System Prompt。
要做：按需检索注入（RAG），每次只带最相关的上下文。

#### 5.3 上下文隔离
- 派生子 Agent 时必须隔离其上下文
- 不要让子 Agent 的对话污染父上下文
- 只返回结果摘要，不是完整对话记录

#### 5.4 不存幻觉引用
- Agent 搭 Agent 时容易产生"这个能力 Claude 原生支持"的幻觉
- 引用的 API、能力、功能点必须经过验证
- 不确定就说"不确定"，不要编

#### 5.5 记忆策略
- 从无记忆开始（纯会话）
- 需要时加 Session 级记忆（`MEMORY.md` 指针索引）
- 只有跨 Session 需求证实后才加持久化记忆
- 记忆只存"不可从代码直接推导"的信息

---

## 可用资源

### 项目内建 Skills（`.claude/skills/`）
本系统已安装大量 Agent 构建相关的 Skill，搭建 Agent 时应优先使用（通过 Skill 工具调用）：

**核心 Agent 模式：**
- `meta-agent-builder` — 构建 Agent 的完整知识库（19 章 Agent 课程速查 + 脚手架引导）
- `agent-creator` — 从模板创建各类 Agent（对话型、研究型、任务型、多 Agent）
- `rag-agent-loop` — 最小 Agent Loop + RAG 知识库 Agent 搭建
- `subagent-pattern` — 子 Agent 上下文隔离模式
- `agent-team` — 多 Agent 团队协作模式
- `autonomous-agent` — 自主运行 Agent 模式

**基础设施层：**
- `tool-use-builder` / `mcp-plugin` — 工具构建
- `memory-system` / `hook-system` / `prompt-pipeline` — 记忆/钩子/Pipeline
- `skill-system` / `permission-system` / `task-system` / `background-task` / `scheduled-task`
- `context-compact` — 上下文压缩
- `error-recovery` — 错误恢复
- `team-protocol` / `worktree-isolation`

### Agent 课程（`learn-claude-code/`）
12 章中英文课程，从 Agent Loop 到自治 Agent 团队。搭建复杂 Agent 时可查阅对应章节。

---

## 开发约定
- PEP 8 编码规范
- 所有公共接口加类型注解
- 注释只写 WHY，不写 WHAT
- 无死代码、无注释掉的代码
- 所有 Tool-Use 逻辑需有测试覆盖

# Backend Driver — 用户本地生成的"工作台适配器"

> Backend driver 是把 commando 接到具体协作平台（飞书 / Notion / 钉钉 /
> 企微 / ClickUp / Linear 等）的代码。**commando 仓库本身不维护多个
> backend driver**——driver 由用户本地的 agent（Claude Code / Codex / Kimi
> CLI 等）按需生成，留在用户自己的 Configuration 仓库里。

## 一句话理解

`commando connect <platform>` ≠ 安装一个 commando 内置 driver。
`commando connect <platform>` = **让你本地的 agent 替你写一个 driver，commit
到你自己仓库**。commando 提供的是**生成框架**，不是 driver 本身。

## 为什么这么设计

| 替代方案 | 问题 |
|---|---|
| commando 维护 N 个官方 driver | LangChain 路线，永远追不完平台变化，仓库被适配层吞掉 |
| 只支持 1 个官方 driver | 把所有非该 backend 用户挡在门外 |
| **生成模式** | commando 维护**生成模板** + **能力词典**；driver 代码本身在用户那里、用户能自己改、用户能 PR 回来作为社区参考 |

LLM 已经足够聪明能读 lark-cli / Notion SDK 文档写出一个 driver。我们的
工作是把"该写成什么样"说清楚，让 LLM 一遍写对。

## Driver 的最小目录结构

```
my-agent/backends/<platform>/
├── manifest.yaml          ← 自报家门：name / provides / 依赖
├── driver.py              ← 实现 capability 域动词
├── README.md              ← 用户/agent 写的"我做了什么取舍"
└── tests/                 ← 推荐有，self-test 用
    └── smoke.py
```

## manifest.yaml

```yaml
name: feishu
type: backend
version: 0.1.0
generated_by: claude-code@2026-06-11
based_on: lark-cli@<version>

# 自报家门提供的 capability（详见 capabilities.md）
provides:
  Documents: [create, read, update, comment, share]
  StructuredData: [list_records, create_record, update_record, subscribe]
  Messaging: [send_text, send_card, send_dm, notify]
  EventStream: [subscribe, unsubscribe]
  Calendar: [create_event, freebusy, list_events]
  Storage: [upload, download, get_url]
  KnowledgeBase: [create_node, read_tree, update_node]

# 该 backend 特有的能力（capability 词典之外的 native API 暴露）
native:
  - bitable.kanban_groupby_person
  - wiki.batch_create_subtree

# 依赖的外部工具
requires:
  cli: lark-cli >= 0.6.0
  python: ">=3.10"
```

## driver.py 的接口（每个 capability 一个方法）

概念形态（不是强制实现）：

```python
class Driver:
    def __init__(self, config: dict, credentials: dict): ...

    # Documents 域
    def documents_create(self, title: str, body: str, **kwargs) -> DocRef: ...
    def documents_read(self, ref: DocRef) -> str: ...
    def documents_update(self, ref: DocRef, patch: str | dict) -> DocRef: ...
    def documents_comment(self, ref: DocRef, text: str) -> CommentRef: ...
    def documents_share(self, ref: DocRef, recipient: UserRef) -> None: ...

    # StructuredData 域
    def structured_data_list_records(self, table: str, filter: dict = None) -> list[Record]: ...
    # ... 等等

    # 必有的元方法
    def manifest(self) -> dict: ...               # 读 manifest.yaml
    def health_check(self) -> bool: ...           # commando run 启动时调
    def native(self) -> Any: ...                  # 暴露 backend-native 调用通道
```

Runtime 通过 `CapabilityRegistry` 把 Skill 里的 `documents.create(...)`
路由到 `driver.documents_create(...)`——Skill 不直接调 driver。

## `commando connect <platform>` 生成流程

### 1. 用户执行

```bash
cd my-agent
commando connect feishu
```

### 2. commando 准备生成 prompt

读取以下材料组装 prompt：

- `commando/docs/capabilities.md`（能力词典）
- `commando/docs/backend-driver.md`（本文档）
- `commando/templates/backend-driver-prompt.md`（生成指令模板）
- 用户配置文件 hint（如 `~/.commando/preferred-cli.yaml` 标了"飞书我用
  lark-cli"）

### 3. commando 把 prompt 喂给用户本地 agent

默认尝试调起 `claude` CLI（即 Claude Code）；找不到则尝试 `codex` / `aider`
等，找不到任何 agent CLI 则提示用户手动复制 prompt 到自己的 LLM 环境。

### 4. Agent 在 my-agent/backends/<platform>/ 写代码

按 prompt 指令：
- 调用 WebFetch 读 platform CLI/SDK 文档
- 按 capability 域逐个实现方法
- 写 manifest.yaml 自报家门
- 写 README.md 说明取舍
- 写 tests/smoke.py 跑通最小用例

### 5. commando 跑自检

```bash
commando connect feishu --verify
```

- 加载新生成的 driver
- 调用 `health_check()`
- 对每个声明的 capability 跑一次 smoke test（创建测试 doc 然后删除等）
- 通过 → 提示用户 commit；失败 → 把错误传回 agent 让它修

### 6. 用户 commit

driver 代码留在 `my-agent/` 仓库里，受用户控制——他可以自己改、可以 PR
回 commando-backends（未来社区仓库）。

## Backend Driver 生成 Prompt 模板（核心）

这个 prompt 是 `commando connect` 真正的"产品"。它必须告诉 agent：

```
你的任务：为 <platform> 写一个 commando backend driver。

参考资料：
1. commando 能力词典：<贴 capabilities.md 全文>
2. commando driver 接口：<贴本文档接口部分>
3. <platform> 官方 CLI/SDK 文档：<URL 列表，让你 WebFetch>

输出物：
- backends/<platform>/manifest.yaml
- backends/<platform>/driver.py
- backends/<platform>/README.md
- backends/<platform>/tests/smoke.py

约束：
1. 只实现你能找到对应文档的 capability 动词——找不到的写到 manifest
   的 provides 之外，**不能伪造**
2. driver.py 必须能独立 import 跑（不能依赖 commando 内部模块）
3. 凭据通过 __init__ credentials 传入，**不要从环境变量或硬编码读取**
4. README.md 里如实记录：哪些 capability 实现了/部分实现/未实现，及原因
5. tests/smoke.py 不要依赖真实凭据——用 mock 跑基础逻辑校验

完成后告诉用户跑 `commando connect <platform> --verify`。
```

**模板设计原则**：约束尽量明确，agent 想偷懒就直接堵住路径；不限制实现
风格。

## commando 出厂的 reference impls（仅 2 个）

| Backend | 路径 | 角色 |
|---|---|---|
| **local** | `commando/reference-backends/local/` | 零配置启动，SQLite + 本地文件。hello-world / 调试 / 没接平台时用 |
| **lark**（飞书）| `commando/reference-backends/lark/` | 从 atu 沉淀；社区 PR 维护；不是"官方支持"，是"参考实现" |

其他 backend（钉钉 / 企微 / Notion / ClickUp / Linear / GitHub Projects 等）
**全部走 `commando connect` 生成模式**。

## Driver 演化路径

1. 用户跑 `commando connect <platform>` 生成 v0.1 driver
2. 用一段时间发现哪些 capability 没实现 / 实现错了 → 用户/agent 改
3. 改完想分享 → PR 到 `commando-backends/<platform>` 仓库（未来）
4. 社区 PR 多了 → 选一份合并成"社区参考实现"
5. **commando 仓库永远不会有 5 个 backend driver**——避免维护漩涡

## 测试与诊断

- driver 必须实现 `health_check()`——`commando doctor` 命令会调用
- 推荐每个 capability 域有一个 smoke test（mock 模式）
- 真实凭据集成测试在用户自己仓库 CI 跑，commando 不替代

## 反模式

- ❌ driver.py 里写业务逻辑 —— 业务逻辑在 Skill，driver 只做适配
- ❌ driver 调用 LLM —— LLM 调用由 Skill 控制
- ❌ driver 跨 backend 共享代码 —— 想共享的话抽到 commando 的 utils，
  不要 driver 之间互依赖
- ❌ 伪造未实现的 capability —— manifest.yaml 声明了就必须真能工作
- ❌ 在 driver 里写 Workbench / Memory 业务规则 —— 那是 Runtime 的事

---

*Backend driver 是 commando "维护成本最低、对用户最透明"的设计选择。
我们不维护、不审核、不官方支持任何具体平台 driver——但提供生成它的
能力词典 + 生成 prompt + 验证工具。这是 commando 不变成另一个 LangChain
的关键保障。*

# Capabilities — 能力词典

> 能力词典是 commando 里**最薄、也最关键**的一层。它给"创建一个文档 /
> 发一条消息 / 写一行记录"这些**业务动作**起一组跨 backend 通用的名字，
> 让同一份 Configuration 能在飞书、Notion、钉钉等不同协作平台上跑起来。

## 一句话理解

Capability ≠ API。Capability = **业务动作的语义名字**。
`Documents.create` 是 capability；`POST /open-apis/docx/v1/documents` 不是。

## 为什么这层薄薄的抽象不能省

如果 Skill 直接调 `lark-cli docs +create`：
- Skill 永远只能跑在飞书
- 测试必须连真实飞书 app
- Onboarding 时无法回答用户"这份 Configuration 在 Notion 上能跑吗"

如果加一层 capability 语义层：
- Skill 写 `documents.create(title, body)`——业务动作而不是 API
- Configuration 声明 `capability_requirements: [Documents.create]`
- Backend 自报家门 `provides: [Documents.create, ...]`
- Onboarding 加载时校验"你 Configuration 要的能力，当前 backend 都有吗"

这层就是这样**轻、薄、不发明 protocol、不做 lowest-common-denominator**——
它只是给 backend 已有的能力起一组通用名字。

## 能力域（commando v0.1 词典）

| 能力域 | 业务含义 | 典型动词 | 飞书实现 | Notion 实现 |
|---|---|---|---|---|
| **Documents** | 可编辑富文本文档 | `create / read / update / comment / share` | lark-cli docs | Notion pages API |
| **StructuredData** | 多维表 / database 类结构化记录 | `list_records / create_record / update_record / subscribe` | lark-cli bitable | Notion databases |
| **Messaging** | 即时通讯消息 / 卡片推送 | `send_text / send_card / send_dm / notify` | lark-cli im | Notion 无 → 跳过 |
| **EventStream** | 实时事件订阅（消息 / 状态变化）| `subscribe / unsubscribe` | feishu WebSocket | Notion webhook |
| **Calendar** | 日程 / 会议 | `create_event / freebusy / list_events` | lark-cli calendar | Notion 无 → 跳过 |
| **Tasks** | 待办事项 | `create_task / list_tasks / complete` | lark-cli task | Notion tasks DB |
| **Storage** | 文件上传 / 下载 / 共享 | `upload / download / get_url` | lark-cli drive | Notion files |
| **KnowledgeBase** | Wiki / 长期知识库 | `create_node / read_tree / update_node` | lark-cli wiki | Notion pages (recursive) |

**注意**：这张表不是"完整 API"。每个能力域只列**核心动词**——backend 想
扩展更多动词随意，但 commando Configuration 只能依赖这些通用动词，否则
就跨不出当前 backend。

## Configuration 怎么声明 requirements

在 `skills/<name>/SKILL.md` frontmatter 里：

```yaml
---
name: xhs-bilingual-bridge
capability_requirements:
  - Documents.create
  - Documents.update
  - Storage.upload
  - Messaging.send_dm
---
```

写法约定：`<能力域>.<动词>`，**只声明你真用到的动词**——避免无谓的耦合。

## Backend driver 怎么声明 provisions

在 `backends/<name>/manifest.yaml`（详见 [`backend-driver.md`](backend-driver.md)）：

```yaml
name: feishu
provides:
  Documents: [create, read, update, comment, share]
  StructuredData: [list_records, create_record, update_record, subscribe]
  Messaging: [send_text, send_card, send_dm, notify]
  EventStream: [subscribe, unsubscribe]
  Calendar: [create_event, freebusy, list_events]
  Storage: [upload, download, get_url]
  KnowledgeBase: [create_node, read_tree, update_node]
```

## Onboarding / Runtime 校验时机

| 时机 | 谁校验 | 校验什么 |
|---|---|---|
| Onboarding Calibration | Onboarding skill | "用户选的 backend 是否能满足建议 Skill 的 requirements"——不满足要提醒换 Skill 或换 backend |
| Configuration 加载 | Runtime | 所有 enabled Skill 的 requirements 是否都被当前 backend 提供——不满足直接 fail-fast |
| Runtime 运行时 | Runtime | 调用 capability 时检查动词存在——不存在 → 报清晰错误，不让 LLM 看见底层 API 错误 |

**fail-fast 是核心原则**：能力缺失必须在 Configuration 加载就报错，不能等
Skill 跑到一半才挂——后者会污染 Workbench 状态。

## Native 逃生舱口（重要）

有些 Skill 就是要榨干特定 backend 的能力（如飞书 bitable 的"看板分组按
人员字段聚合"这种富功能）。这种情况下：

```yaml
# SKILL.md frontmatter
capability_requirements:
  - StructuredData.list_records       # 通用部分
backend_native:
  - feishu.bitable.kanban_groupby      # 显式标注 backend 专属调用
backend_lock: feishu                   # 声明这个 skill 不可移植
```

**规则**：
- `backend_native` 字段允许 Skill 调用 backend 原生 API（如 `backend.lark_cli(...)`）
- 一旦使用 `backend_native`，必须同时设 `backend_lock`——这个 Skill 就只能
  在指定 backend 上跑
- Onboarding / Runtime 加载时把这种 Skill 标记为"backend-locked"，提示用户

这给"想跨 backend 跑"和"就是要榨干当前 backend"两种 Skill 都留了合法位置。

## 如何扩展能力词典

社区想增加新的能力域（如 `Forms` / `Surveys` / `Analytics`）：

1. 在 commando 仓库开 issue 说明用例（至少 2 个真实 Skill 需要它）
2. 提交 PR 改本文档：新增能力域 + 列动词
3. 至少 2 个 backend driver 同时支持后才能算"标准化"，否则只能 backend-native

**反例**：不要为某一个具体 Skill 单独加能力域。词典是公共契约，不是 dump 区。

## 工程实现层（指引 Runtime 实现者）

Runtime 内部用一个 `CapabilityRegistry` 单例管理：

```python
# 概念性，非实际代码
class CapabilityRegistry:
    def register(domain: str, verb: str, backend_name: str, handler: Callable)
    def call(verb_fqn: str, *args, **kwargs)        # "Documents.create" → 路由到当前 backend handler
    def validate(requirements: list[str]) -> ValidationReport
```

- Skill body 里 `documents.create(...)` 由 Runtime 注入的 client 翻译成
  `registry.call("Documents.create", ...)`
- Backend driver 启动时调 `registry.register(...)` 注册自己提供的所有动词
- Configuration 加载时调 `registry.validate(...)` 跑完整校验

详见 [`backend-driver.md`](backend-driver.md) 的"driver 接口"章节。

---

*能力词典是 commando 跨平台叙事的基石。词典宽了就退化成"另一个 SDK 适配
层"，词典窄了用户榨不出 backend 能力——保持 6-8 个核心域 + 显式逃生舱口
是当前最优解。*

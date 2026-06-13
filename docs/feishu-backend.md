# Feishu Backend — Reference Implementation

> 飞书 backend 是 commando 的**第一个 reference backend driver**——把
> Configuration 物化为飞书 Wiki 文档 + Bitable + IM 事件订阅。
> v0.1 提供 dry-run 工具 `tools/materialize.py`；真正执行依赖
> [lark-cli](https://github.com/larksuite/lark-cli) 和你跑过的
> `commando connect feishu` 凭据。

## 一句话理解

`commando materialize --backend feishu` 把 `./my-agent/` **本地**目录转成
**飞书工作区**里"用户日常看的那些东西"——但 source of truth 仍是本地。
飞书是镜像 + 协作面板。

## materialize 真做了什么

| Action | 飞书对象 | 由谁产生 |
|---|---|---|
| upsert Wiki node 「Charter」 | Wiki 文档 | charter.md 单向同步 |
| upsert Wiki sub-node 「Skills」 + 每 skill 一个子节点 | Wiki 子页面 | skills/*/SKILL.md 单向同步 |
| create Bitable app 「Workbench」（含 4 视图）| Bitable | tools/feishu-bitable-workbench-schema.json |
| insert template rows | Bitable rows | schedule.yaml 的 tasks |
| register IM bot listener | 事件订阅 | bot_app 凭据 |

详细 schema 见 [tools/feishu-bitable-workbench-schema.json](../tools/feishu-bitable-workbench-schema.json)。

## "一张表两种 row"如何在 Bitable 里实现

回顾 [docs/scheduler.md](scheduler.md)：scheduler 物化为**一张 Workbench
bitable + `type` 字段区分 template / instance**。

- `type = template` 行：来自 schedule.yaml 的任务**声明**——cron、skill 列表、
  是否需人审。改这些行 = 改 Schedule 配置（runtime 自动 sync back）。
- `type = instance` 行：每次 trigger 触发由 Runtime 写入——started_at /
  ended_at / status / artifact_uri / notes。**不要手动改 instance 行的状态
  字段**，runtime 是 owner。

4 个 view 各看什么：

| View | 过滤 | 用途 |
|---|---|---|
| Calendar | 全部 | 周/月视图看 template 节奏 + instance 完成情况 |
| Kanban | `type = instance` group by status | 看当前 instance 在 Inbox/WIP/WaitingApproval/Done/Blocked 哪一栏 |
| Gantt | 全部 with date range | 本周一览 |
| Table | sort started_at desc | 全量回顾，做数据分析 |

## artifact_uri：审稿按钮跳的链接

每条 instance 必有 `artifact_uri` 字段。这是 dashboard 上「审稿」按钮跳的
位置。对于 Feishu backend：

- 通常是 `https://feishu.cn/docx/<token>`——agent 调 `lark-cli docs +create`
  写产物（草稿）+ 拿到 URL + 填回 instance 行
- 也可以是 `file://` 当 Skill 把产物写到本地（Local backend 模式）

dashboard 不关心是哪种——拿到 URI 就 openUri。

## IM 卡片：状态变化的推送通知

bot_app 注册了 `bitable.record_changed` 事件订阅。每次 instance row 状态
变化（如 WaitingApproval → 出现）→ bot 推 IM 卡片给 Qihang：

```
┌────────────────────────────────────────┐
│ 阿土                                    │
│ xhs_draft_tue · 等你审稿                 │
│ ─────────────                           │
│ 11:00 跑完了，1 篇笔记初稿。              │
│                                          │
│ [ 审稿 ↗ ]  [ 看状态行 ]                 │
└────────────────────────────────────────┘
```

主按钮 coral，跳 artifact_uri；副按钮跳 workbench_uri（让你能看到 / 改状态）。

## 两个 Feishu app 的角色分工

commando Feishu backend **必须**用两个 app（参考 atu 半年实跑经验）：

| App | 干嘛用 |
|---|---|
| **user_app** | 你自己身份的 OAuth · 用于 bitable / wiki / drive 读写（要你的工作区权限） |
| **bot_app** | 阿土独立身份 · 用于 IM 卡片推送 + 事件订阅 |

两个 app 的凭据放在 `~/my-agent/credentials/feishu_credentials.yaml`（gitignore）。

`commando connect feishu` 流程会让用户本地 agent 走完 OAuth + 写入这两份
凭据。详见 [docs/backend-driver.md](backend-driver.md)。

## v0.1 状态：dry-run only

v0.1 的 `tools/materialize.py` **默认不实际执行**——它打印 lark-cli 命令
让你看到 commando 计划在飞书做什么。你可以：

1. 手动 copy-paste 命令到 terminal 执行（**调试用**）
2. 或加 `--apply` 让脚本一条条 invoke lark-cli（要求 lark-cli 已 auth）

v0.2 会做的：
- 状态翻转回流（在 dashboard 上直接改状态 → 同步到 bitable）
- 增量 materialize（不破坏既有 instance 行的情况下加新 template）
- materialize 后自动跑健康检查

## 怎么试

```bash
# 1. 看 dry-run plan
python tools/materialize.py --agent-dir ./my-agent --backend feishu

# 2. 真正执行（需要 lark-cli auth 好）
python tools/materialize.py --agent-dir ./my-agent --backend feishu --apply
```

## 为什么飞书是 v0.1 first

| 理由 | 说明 |
|---|---|
| atu 已经在跑 | 6 个月真实使用，所有踩坑都过了一遍 |
| lark-cli 已经覆盖 2500+ API | 几乎不用写适配代码 |
| Bitable 多视图原生强 | 不用自建 calendar/kanban/gantt——飞书都有 |
| 国内用户密度高 | 小红书/X 推广受众的工具栈大概率包含飞书 |

但 commando 设计上是 **backend-agnostic**——v0.2+ 会加 Notion / 钉钉 /
企微 / Linear，机制相同：reference driver + dry-run plan + apply。

详见 [docs/backend-driver.md](backend-driver.md)。

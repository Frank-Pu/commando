# Scheduler — 数字员工的产品表面

> Configuration 物理上是个目录，但对用户来说"这个数字员工存在"的体感
> 来自 **scheduler**——一个能看见过去/现在/未来三件事的地方。
> 这是 commando 区别于"另一个 agent 框架"的关键产品决定。

## 一句话理解

Scheduler 同时承担三件事：

| 心智功能 | 用户潜台词 |
|---|---|
| **过去** | "它今天给我干了啥" |
| **现在** | "它现在在忙啥，卡在哪了" |
| **未来** | "它待会儿 / 明天打算干啥" |

三件事不在一个屏幕里同时呈现，agent 在用户脑子里就活不起来。

## 文件位置

- 声明：Configuration 目录根下的 `schedule.yaml`
- 运行实例：Workbench（默认 backend 渲染，例如 Feishu bitable）
- 物理上**一张表，两种 row 类型**（见下）

## 核心模式：一张表，两种 row 类型

用户在飞书 bitable / Notion database 里看到的是**一张统一的 scheduler 表**，
背后通过 `type` 字段区分：

| type | 含义 | 谁写 | 例子 |
|---|---|---|---|
| `template` | 任务的**声明** | Configuration（人手写或 Onboarding 产出） | "每天 08:22 跑 morning_sense" |
| `instance` | 任务的**一次实际执行** | Runtime 在 trigger 触发时自动写 | "2026-06-10 08:22 跑了 morning_sense → Done" |

这个 trick 解决了"用户希望感知一个 scheduler"和"工程上 Schedule 和
Workbench 是分开概念"的张力——**表面统一，数据正交**。

## schedule.yaml 格式

```yaml
version: 0.1
timezone: Asia/Shanghai

tasks:
  - id: morning_sense
    description: 扫 Reddit/HN 头条，LLM 4 维打分，入选题池
    trigger:
      type: cron
      cron: "22 8 * * *"
    skill: reddit-source-mining
    inputs:
      subreddits: [r/languagelearning, r/LearnEnglish]
    workbench_status_init: WIP
    on_complete: Done
    on_failure: [notify_im, status:Blocked]

  - id: xhs_draft
    description: 把"已选"的选题做成小红书 Bilingual Bridge 笔记
    trigger:
      type: chain
      on: 选题池.row_status_changed
      condition: status == "已选"
    skill: xhs-bilingual-bridge
    requires_human_approval: true        # 对外产物必经人审

  - id: weekly_reflection
    description: 周日晚跑数据复盘 + 更新 Semantic Memory
    trigger:
      type: cron
      cron: "0 19 * * 0"
    skill: weekly-reflection
```

字段说明（仅最小集）：

- `trigger.type` 必为 `cron` / `chain` / `event` / `manual` 之一
- `requires_human_approval: true` 强制经过 IM 卡片审稿才往下走（commando
  全局红线对应字段）
- `skill` 引用 `skills/<name>/SKILL.md`
- `workbench_status_init` / `on_complete` / `on_failure` 控制 Workbench
  状态机推进

## 四种视图（让 backend driver 实现）

scheduler 表必须暴露 4 种视图（backend 视支持情况尽力实现，不支持降级为
表格视图 + 提示）：

| 视图 | 解决什么 | 类比 |
|---|---|---|
| **日历视图** | "未来 1-2 周节奏" | Google Calendar 周视图 |
| **看板视图** | "现在每件事卡在什么状态" | Trello / Jira 看板 |
| **甘特图视图** | "本周整体节奏一览" | Notion timeline |
| **表格视图** | "全量 backlog 与历史" | 默认表格 |

这四种映射到飞书 bitable 都是原生支持的（一表多视图），Notion / ClickUp /
钉钉智能表格也都支持。Slack / 纯 IM 类 backend 降级为"每日摘要 + 状态变化
推送"。

## materialize 协议

```bash
commando materialize                       # 把 schedule.yaml + Workbench 渲染到当前 backend
commando materialize --dry-run             # 只看会改什么
commando materialize --backend feishu      # 显式指定
```

行为 terraform 风格：
- 第一次跑 → 创建 bitable + 4 视图 + 字段
- 后续跑 → diff & patch，不删用户的 instance 数据
- Configuration 改了（加 Skill / 改 Schedule）→ 重跑 materialize 同步

## 本地 fallback：`commando dashboard`

用户还没接 backend 时（hello-world / 调试阶段），跑：

```bash
commando dashboard
```

起一个 localhost HTML（~300 行 HTML+JS），读本地 `workbench/*.json`，显示：

- 今日 instance 列表
- 本周 template 日历
- 最近日志流

**故意做得朴素**——它是"工地"，不是"展厅"。展厅是 backend 那份。
避免诱导用户停留在 local，也避免我们被卷入"做 UI"。

## 让 scheduler 有温度的两个低成本招数

1. **Agent 身份注入 instance**：每行 instance 的"执行者"字段填 Charter 里
   定的 agent 名字（如阿土）和头像，而不是冷冰冰的"system"。看起来就像
   看真同事的任务表。
2. **IM 卡片作为 scheduler 的推送通知**：状态变化（Done / Blocked /
   需审稿）触发 backend 的 IM 卡片，主按钮跳回 scheduler 对应行。

这两个加起来，用户体感从"我装了个 framework"变成"我多了个会按时上班的
实习生"——这是产品成立的瞬间。

## Role-specific 节奏建议在哪看

各 playbook 给"这个角色的日常班次"具体建议。比如
[`playbooks/growth-partner.md`](../playbooks/growth-partner.md) 决议 4
列出了独立产品增长合伙人的 8-9 个推荐 task 时点。

---

*Scheduler 是 commando 唯一面向"日常感知"的产物，所以它的设计要更偏
PM 不偏 engineer——少抽象，多让人一眼看懂。*

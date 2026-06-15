# Event Bus — 活动流与 IM 推送

> commando 里所有"agent 在做什么"的事件都汇聚到**一处** —— Episodic
> Memory。Dashboard 的 Activity tab 是它的实时投影；IM 推送是它的另一个
> 订阅者。这两件事**不是两套系统**，是同一条事件流的两个 sink。

## 一句话理解

**Episodic Memory 就是 event bus**。

- 写 Episodic 的代码（Skill / Runtime）= 事件生产者
- 读 Episodic 的代码（Dashboard / IM Router）= 事件消费者
- "通过飞书发送实况" = 多挂一个 IM Router subscriber + 配 routing rules

## 架构图

```
┌─ Skill execution / Runtime ────────────┐
│                                         │
│   morning_sense ran → 12 candidates     │
│   xhs_draft_tue ran → artifact ready    │
│                                         │
└──────────────────┬──────────────────────┘
                   │ append-only
                   ▼
┌─ Episodic Memory ──────────────────────┐
│  my-agent/episodic/<date>.jsonl         │
│                                         │
│  {ts, level, skill, task_id, message,   │
│   duration_ms, artifact_uri, ...}        │
└────────┬───────────────────────┬────────┘
         │                       │
         │ poll                  │ poll
         ▼                       ▼
┌─ Dashboard ────────┐  ┌─ Event Router ──────────┐
│  Activity tab      │  │  evaluate rules in       │
│  (live projection) │  │  event-routing.yaml      │
└────────────────────┘  └────────┬─────────────────┘
                                 │ matched
                                 ▼
                        ┌─ IM Connector ──────────┐
                        │  im-feishu / im-dingtalk│
                        │  / im-slack / ...        │
                        └────────┬─────────────────┘
                                 ▼
                          用户的 IM client
```

## Event 长什么样

最小 schema（与 Activity tab 显示的字段一致）：

```jsonc
{
  "event_id": "atu-2026-06-14T11:02:34",
  "ts": "2026-06-14T11:02:34+08:00",
  "agent_id": "atu",
  "level": "waiting",          // trigger | running | done | waiting | idle | im
  "skill": "xhs-bilingual-bridge",
  "task_id": "xhs_draft_tue",
  "message": "artifact 已提交飞书 docx · 等你审稿",
  "duration_ms": 107000,
  "artifact_uri": "https://feishu.cn/docx/...",
  "workbench_uri": "https://feishu.cn/base/..."
}
```

详见 [`docs/memory.md`](memory.md) 的 Episodic Memory 章节——event-bus 物理
上就是 `episodic/<date>.jsonl` append-only 文件。

## Routing 规则文件 · event-routing.yaml

用户**手动编辑**，决定哪些事件被推到哪个 IM。

物理位置：`my-agent/event-routing.yaml`（和 charter.md / schedule.yaml 同级）

样例见 [`examples/lemingle-growth-partner/event-routing.yaml`](../examples/lemingle-growth-partner/event-routing.yaml)
（如果没有，去 [`my-agent/event-routing.yaml`](../my-agent/event-routing.yaml)）。

核心结构：

```yaml
rules:
  - name: <规则名>
    when:                      # 匹配条件（AND）
      level: <level>           # 单值或数组
      skill_in: [<skill>, ...]
    push_to: [<destination>]
    template: |                # 可选；不写则用默认渲染
      🔔 {agent_name}
      {message}
      [打开 ↗]({artifact_uri})

destinations:
  feishu_im_dm:
    via_connector: im-feishu
    channel: dm_qihang
    rate_limit: 30/hour        # 防 IM 骚扰
    quiet_hours: [22:00, 08:00] # 静默时段
```

**评估语义**：
- 规则**自上而下**首次匹配生效
- 不匹配任何规则 → **不推送**（默认沉默）
- 同一事件**多 destination** push 会去重 event_id 避免重复

## IM Connectors

每个 IM 平台的 connector 实现 [`capabilities.md`](capabilities.md) 里的
`Messaging.send_dm` / `Messaging.send_card` / `Messaging.notify`。

| Connector | 状态 | 物理位置 |
|---|---|---|
| **im-feishu** | placeholder（占位）| [`connectors/im-feishu/`](../connectors/im-feishu/) |
| im-dingtalk | 等社区贡献 | — |
| im-slack | 等社区贡献 | — |
| im-discord | 等社区贡献 | — |

新接入一个 IM 平台的标准流程（参考 [`docs/backend-driver.md`](backend-driver.md)）：

```bash
commando connect im-feishu     # 用本地 agent 生成 driver
# (然后在 event-routing.yaml 里引用)
```

## 设计决策的几个关键约束

### 1. event-bus = Episodic Memory，不是新东西

我们不引入新组件——Episodic Memory 已经在 [`docs/memory.md`](memory.md) 定义过。
event-bus 是它的**别名**，强调"被多个 subscriber 读"的角度。

### 2. Router 是无状态规则引擎，可独立测试

```bash
# dry-run：评估一个事件被推到哪里、不真发
python tools/route.py --agent-dir ./my-agent --event-id atu-2026-06-14T11:02:34 --dry
# 输出： would push to feishu_im_dm via template "waiting_for_review"
```

### 3. Connector 不和 Router 耦合

Router 只知道 `feishu_im_dm` 是个 "destination ID"。Connector 怎么把
event 翻译成飞书卡片是 connector 自己的事。Router 不写飞书 API。

### 4. 静默时段 + 速率限制 是默认必有

新接入用户**默认配置**就有 `rate_limit: 30/hour` + `quiet_hours: [22:00, 08:00]`。
没人想周六凌晨被 IM 弹炸。

## v0.1 状态（坦诚说）

| 组件 | 状态 |
|---|---|
| ✅ Episodic Memory schema | [`docs/memory.md`](memory.md) 写好了 |
| ✅ Dashboard Activity tab | mock event 实现，演示 bus 投影 |
| ⏳ Event Router engine | 本文档定 spec，**未工程化** |
| ⏳ event-routing.yaml | 占位样例见 my-agent/ |
| ⏳ IM connectors | 占位 README 见 connectors/im-feishu/ |
| ⏳ tools/route.py | 占位（未实现） |
| ⏳ rate-limit / quiet-hours / dedup | 已在 spec，未工程化 |

## 为什么先做 dashboard 视觉而非 IM connector

1. dashboard 用户**无需 OAuth / 无需注册任何东西**就能用
2. IM 推送需要**每个平台单独工程**（飞书 vs 钉钉 vs Slack 各一套）
3. dashboard 上看清楚 event 流之后再决定**哪些值得推 IM**——避免"为了推而推"

所以 v0.1：**dashboard 是给所有用户的**，IM 推送是给"想 + 配置 OK"的人的。
这一定不能调换顺序。

## 反模式

- ❌ **把所有 event 都推 IM**：30 分钟你就关掉 commando 推送了。Routing 默认沉默是对的
- ❌ **Router 直接调 lark-cli**：耦合死。永远经过 IM connector 抽象层
- ❌ **dashboard 上看不到 event，但 IM 收到了**：违反 single source of truth
- ❌ **event_id 不稳定**：导致 IM 重复推送同一事件。生产时必须含 agent_id + ts

## 跨文档关系

- [`docs/memory.md`](memory.md) — Episodic Memory schema = event bus 物理形式
- [`docs/capabilities.md`](capabilities.md) — Messaging 能力域定义
- [`docs/connectors.md`](connectors.md) — Connector 概念（Backend vs Source）；IM connector 算 Source 一类
- [`docs/backend-driver.md`](backend-driver.md) — IM connector 也走 `commando connect` 生成流程

---

*Event Bus 这一层最大的价值不是"加了一个推送功能"——是把"agent 在做
什么"这件事统一成一条流，让 dashboard / IM / 未来的其他 UI（手表？车
载？）都从同一处订阅。这是 commando 走向 multi-surface 的地基。*

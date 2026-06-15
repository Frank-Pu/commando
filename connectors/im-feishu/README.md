# im-feishu — 飞书 IM 推送 connector（占位）

> ⏳ **v0.1 占位** —— 当前**没有 driver 实现**，只有契约说明。
> v0.2 `commando connect im-feishu` 上线后会生成 `driver.py` 在这个目录下。

## 这个 connector 做什么

把 commando 的 event（参考 [`docs/event-bus.md`](../../docs/event-bus.md)）
通过**飞书 IM 卡片**推给用户。订阅 Episodic Memory，按用户的
`event-routing.yaml` 规则匹配后调用 `lark-cli im` 发卡片。

## 契约（`commando connect im-feishu` 生成时遵守）

### 必须实现的 capability 动词（详见 [`docs/capabilities.md`](../../docs/capabilities.md)）

| Capability | 含义 |
|---|---|
| `Messaging.send_dm` | 给指定用户发文本 DM |
| `Messaging.send_card` | 发飞书 V2 交互卡片（含按钮）|
| `Messaging.notify` | 触发未读红点（无内容，仅唤醒）|

### 推荐的方法签名

```python
class FeishuIMConnector:
    def __init__(self, config, credentials): ...

    def send_dm(self, user: str, text: str) -> str:
        """发文本 DM，返回 message_id。"""

    def send_card(self, user: str, title: str, body: str,
                  primary_action: Optional[dict] = None,
                  secondary_actions: Optional[list] = None) -> str:
        """
        发 V2 卡片。primary_action 例子：
            {"text": "审稿 →", "url": "https://feishu.cn/docx/..."}
        secondary_actions 是辅助按钮列表，同结构。
        """

    def notify(self, user: str) -> None:
        """只触发红点，不发内容（用于低优先级事件）。"""

    def manifest(self) -> dict:
        return {
            "name": "im-feishu",
            "type": "source",
            "provides": {
                "Messaging": ["send_dm", "send_card", "notify"]
            },
            "requires": {"cli": "lark-cli >= 0.6.0"},
        }
```

### 凭据

复用 [`my-agent/connectors.yaml`](../../examples/lemingle-growth-partner/) 里的
`feishu_credentials`——飞书 IM 用 **bot_app** 身份（不是 user_app）。
配置存放原则见 [`docs/connectors.md`](../../docs/connectors.md) "凭据管理"
章节。

## 卡片设计参考（atu 已验证的视觉）

每条规则的 `template` 渲染成飞书卡片：

```
┌─ 🔔 阿土 ────────────────────────────┐
│ xhs_draft_tue · 等你审稿             │
│ ──────────────                       │
│ 11:00 跑完了 · 1 篇笔记初稿          │
│ artifact 已提交飞书 docx             │
│                                       │
│ [ 审稿 ↗ ]  [ 看状态行 ]              │
└───────────────────────────────────────┘
```

- 主按钮 **coral** 实心 → 跳 `artifact_uri`（草稿文档）
- 副按钮 outline → 跳 `workbench_uri`（任务状态行）
- 文案来自 routing rule 的 `template`，变量来自 event 字段

详见 [`docs/event-bus.md`](../../docs/event-bus.md) 的 routing 章节。

## 关键约束（spec 必有，driver 必遵守）

| 约束 | 由谁负责 |
|---|---|
| `event_id` 去重（5 分钟窗口）| Router |
| `rate_limit` 检查（默认 30/hour）| Router 在调用 connector 前校验 |
| `quiet_hours` 静默 | Router 跳过推送 |
| 失败重试（exponential backoff，最多 3 次）| Connector |
| 失败之后写回 Episodic（`delivery_failed: true`）| Connector |

## v0.2 期望的生成流程

```bash
cd my-agent
commando connect im-feishu
# → 启动 OAuth (复用 user_app + bot_app)
# → 让本地 agent 读 lark-cli im 文档
# → 生成 connectors/im-feishu/driver.py + manifest.yaml
# → 运行 smoke test (发一条 DM 给自己)
# → commit
```

详见 [`docs/backend-driver.md`](../../docs/backend-driver.md)（IM connector
和 backend driver 走同一套生成机制）。

## 为什么 v0.1 不直接做

| 原因 | 说明 |
|---|---|
| **凭据流程未自动化** | `commando connect <X>` 还没工程化（依赖 oauth + 本地 agent） |
| **Router engine 未实现** | 没有 router 就没人调 connector |
| **dashboard 已能演示流的视觉** | 视频 demo 不依赖 IM 也够 |
| **避免 IM 骚扰被 reverse-engineer 抄走** | 这套设计真正有差异化的不是发 IM，是**routing 哲学**（默认沉默、quiet hours、event_id dedup）。文档先公开这套哲学，工程留到 v0.2 |

---

*占位 README 已立 spec · 等 `commando connect im-feishu` 生成 driver 来填坑。*

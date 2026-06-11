# Connectors — 数字员工的对外连接层

> Configuration 里所有"和外部世界打交道"的事都走 Connector：
> 工作台（Workbench backend）、数据源（Reddit / RSS / X / 外刊订阅）、
> 输出通道（IM 推送 / 邮件）、生成 API（图像 / 音频）。

## 一句话理解

Connector = 外部世界的一个**已配置的接入点**。它 = 实现代码（driver）+
一份本地配置（凭据、参数）+ 一组它声明能提供的 capability。

## 两类 Connector

| 类型 | 作用 | 数量 | 特殊性 |
|---|---|---|---|
| **Backend connector** | 承载 Workbench + Scheduler 物化 + 持久化 | **每个 Configuration 必须且只能有 1 个 active** | 必须实现核心 capability 域；详见 [`backend-driver.md`](backend-driver.md) |
| **Source connector** | 数据源 / 输出通道 / 生成 API | 任意多个 | 只需声明它提供的 capability |

**为什么 Backend 是特殊的**：它不只是数据源——它还是用户**日常感知数字
员工的地方**（详见 [`scheduler.md`](scheduler.md)）。所以一个 Configuration
只能有 1 个 active backend，否则用户不知道该看哪一个 dashboard。

## 文件位置

```
my-agent/
├── connectors.yaml                   ← 总声明
├── backends/                         ← Backend driver 代码（用 commando connect 生成）
│   ├── feishu/
│   │   ├── manifest.yaml
│   │   └── driver.py
│   └── local/                        ← commando 出厂 reference impl
│       └── ...
└── connectors/                       ← Source connector 代码（同样按需生成或社区共享）
    ├── reddit/
    ├── rss/
    └── wanx/
```

## connectors.yaml 格式

```yaml
version: 0.1

backend:
  active: feishu                       # 当前 Configuration 用哪个 backend
  feishu:
    workspaces:                        # 飞书特有：哪些 wiki/bitable 给阿土用
      wiki_space_id: "..."
      bitable_app_token: "..."
    credentials_ref: feishu_credentials # 引用 credentials/feishu_credentials.yaml

sources:
  - name: reddit
    driver: reddit                     # 引用 connectors/reddit/
    config:
      subreddits: [r/languagelearning, r/LearnEnglish]
      min_upvote: 50
    credentials_ref: reddit_credentials

  - name: outlet_rss
    driver: rss
    config:
      feeds:
        - https://www.economist.com/...
        - https://www.theatlantic.com/...

  - name: wanx_image
    driver: wanx                       # 通义万相图像生成
    config:
      style: notes
    credentials_ref: wanx_credentials
```

## 凭据管理

- 凭据文件位置：`my-agent/connectors/credentials/<ref>.yaml`
- **这个目录必须 gitignore**——connectors.yaml 里只放 `credentials_ref`，
  实际 token / API key 在 gitignore 的凭据文件里
- 凭据文件最简结构：

```yaml
# credentials/feishu_credentials.yaml
user_app:
  app_id: cli_a9660c7799795cba
  app_secret: ...
  user_access_token: ...               # 通过 lark-cli auth login 一次性拿到
bot_app:
  app_id: cli_a97223058f381bb4
  app_secret: ...
```

**约定**：commando 不替代秘密管理服务。多人协作场景下，请用 1Password CLI /
op-secret-manager / Vault / 飞书 ScopeStore 等导出到这个文件，不要把
真凭据 commit 进 git。

## Connector 提供的 capability

每个 Connector 在 `<driver>/manifest.yaml` 里自报家门：

```yaml
# backends/feishu/manifest.yaml
name: feishu
type: backend
provides:
  Documents: [create, read, update, comment, share]
  StructuredData: [list_records, create_record, update_record, subscribe]
  Messaging: [send_text, send_card, send_dm, notify]
  EventStream: [subscribe, unsubscribe]
  # ... 详见 capabilities.md

# connectors/reddit/manifest.yaml
name: reddit
type: source
provides:
  ContentSource:
    - list_posts          # 按 sub + 时间窗拉帖
    - get_comments        # 拉某帖 top 评论
    - search              # 关键词搜帖
```

这给 Skill 一个语义化的依赖声明能力——`xhs-bilingual-bridge` 声明依赖
`ContentSource.list_posts` 而不是 `reddit.subreddit.top`，未来换 HN/Twitter
源就不必改 Skill。

详见 [`capabilities.md`](capabilities.md)。

## 加载与校验时机

| 时机 | 行为 |
|---|---|
| `commando run` 启动 | 读 connectors.yaml → 加载所有 driver → 调 manifest 注册 capability → 校验所有 Skill requirements 是否被满足 |
| Skill 调用 capability | Runtime 路由到正确的 connector（多个 connector 提供同一 capability 时按 connectors.yaml 顺序优先）|
| Connector 凭据过期 | driver 自己负责续 token（如 Reddit OAuth refresh-token）；commando 不替代 |

## Connector 的诞生路径

| 路径 | 何时用 | 怎么做 |
|---|---|---|
| **commando 出厂** | `local` backend / 未来可能的最小常用 connector | 直接在 commando 仓库里 |
| **`commando connect <platform>` 生成** | 用户首次接入新 backend | 让用户本地 agent（Claude Code/Codex）读 platform CLI 文档生成 driver；详见 [`backend-driver.md`](backend-driver.md) |
| **社区贡献** | 已有用户写过的 connector | PR 到 commando-connectors 仓库（未来）；当前手动 git clone 进 connectors/ |

## Source Connector 写起来比 Backend 简单很多

Source connector 不需要承担 Workbench 物化责任，只需要：

1. 一个 `manifest.yaml` 自报 capability
2. 一个 `driver.py` 实现这些 capability 的核心方法
3. 一份 `credentials.example.yaml` 告诉用户要填什么

所以社区 PR 主要会集中在 Source connector 上（Reddit / X / HN / Substack /
RSS / 各家生成 API 等），而 Backend connector 数量有限且工程复杂——
让 backend driver 由用户本地 agent 当场生成是合理的。

## 反模式

- ❌ Backend connector 之间互通数据 —— 通过 capability 域用，不要写 backend
  间适配代码
- ❌ Connector 里写业务逻辑 —— 业务逻辑在 Skill，Connector 只做"原始接入"
- ❌ Connector 直接调用 LLM —— LLM 调用由 Skill 控制，不能藏在 connector 里
- ❌ Connector 凭据 hardcode —— 永远走 `credentials_ref` 引用 gitignore 文件
- ❌ 在 connectors.yaml 之外的地方读凭据 —— 这是审计的钩子，别绕

---

*Connectors 是 commando 中"外部宇宙的接口面板"——它该薄、该明确、该
让 Skill 通过 capability 而非具体 API 名调用。写得好的 Connector 你能
拿到任何 Configuration 里直接用；写得糟的 Connector 把 Configuration
锁死在某个 backend。*

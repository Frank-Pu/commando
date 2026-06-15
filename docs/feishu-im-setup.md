# 飞书 IM 接入指南（v0.1 手动 setup）

> 让你 dashboard Activity tab 里标 `↗ IM` 的 event 真的推到你飞书。
> 整套首次约 15 分钟，绝大部分时间在飞书开放平台填表单。
>
> 之后任何新 agent 复用同一个 bot，0 重设。

## 它最终长什么样

跑通后，你飞书里那个 bot（建议起名 `阿土` 或 `commando-agent`）会给你 DM：

```
┌─ 🔔 阿土 ─────────────────────────────┐
│ xhs_draft_tue · 等你审稿              │
│ 11:00 跑完了 · 1 篇笔记初稿            │
│ artifact 已提交飞书 docx              │
│                                        │
│ [ 审稿 → ]  [ 看状态行 ]               │
└────────────────────────────────────────┘
```

主按钮 coral 实心 → 跳 artifact docx。副按钮跳 workbench 状态行。

## 前置

- 飞书账号（国内 feishu.cn 或海外 larksuite.com 任一）
- macOS / Linux + Python 3.9+
- `pip install pyyaml`

---

## Step 1 · 装 lark-cli

```bash
brew install lark-cli                          # macOS 推荐
# 或：
npm install -g @larksuiteoapi/lark-cli         # 跨平台

lark-cli --version                              # 验证
```

---

## Step 2 · 在飞书开放平台创建"自建应用"

1. 打开 https://open.feishu.cn/app （海外版：https://open.larksuite.com/app）
2. 点 「创建自建应用」
3. 填：
   - **应用名称**：`阿土` （或任何你喜欢的）
   - **应用描述**：`我的 commando 数字员工`
   - **图标**：可上传，也可暂时不传
4. 创建完进入应用详情页
5. 进 「凭证与基础信息」 → 复制以下两项备用：
   - **App ID** （`cli_xxxxxxxxxx`）
   - **App Secret** （只展示一次，复制好）

---

## Step 3 · 申请权限（scope）

「权限管理」→ 「API 权限」→ 搜索并申请：

| Scope 名 | 干嘛用 | 必须 |
|---|---|---|
| `im:message:send_as_bot` | bot 身份给你发 IM 卡片 | ✅ |
| `im:chat:readonly` | 读取 bot 在哪些 chat 里（拿 chat_id 用） | ✅ |
| `im:resource` | 卡片里挂图片/文件 | 可选 |
| `im:message:readonly` | 读 bot 收到的消息（v0.2 双向交互再加）| 暂不需要 |

申请之后**等审批**——个人自建应用通常 1 分钟内自动通过。

---

## Step 4 · 开启机器人能力

「应用能力」→ 「机器人」→ 开关打开。

可以选择加几句**欢迎消息**，但不影响后面的功能。

---

## Step 5 · 创建版本并发布

「版本管理与发布」→ 「创建版本」：
- 版本号填 `1.0.0`
- 版本描述填 `initial`
- 「申请发布」

如果是**个人**应用（仅自己用）：审批人是你自己，秒过。
如果是**企业**应用：需要管理员审批，可能要等几分钟到一天。

---

## Step 6 · 把 bot 加到你自己飞书

等版本发布完（绿色 ✅）→ 打开飞书 → 「工作台」→ 顶部搜你的应用名 → 「添加」。

加完之后侧边栏会出现 bot 的图标，可以直接点开 DM。

---

## Step 7 · 给 bot 发一条 `hi`

DM 里随便发一条消息（"hi" 也行）。

> 这一步告诉 bot 你是谁，让 bot 拿到一个和你 1:1 的 chat。下一步抓 chat_id 时找的就是这个。

---

## Step 8 · 用 lark-cli 登录 + 抓 chat_id

```bash
# 用刚才的 App ID + App Secret 登录
lark-cli auth login \
  --app-id <your-app-id> \
  --app-secret <your-app-secret>

# 列出 bot 看得到的所有 chat
lark-cli im +chats-list --profile <your-app-id>
```

输出里找 `chat_type: p2p` 的那一行（就是你和 bot 的 1:1 DM），复制 `chat_id`（`oc_xxxxxxxxxxxx...`）。

---

## Step 9 · 写凭据文件

在 `my-agent/credentials/feishu.yaml` 写：

```yaml
bot_app:
  app_id: cli_xxxxxxxxxxxxxxxx          # Step 2 拿的
  app_secret: xxxxxxxxxxxxxxxxxxxxxxx    # Step 2 拿的
  notify_chat_id: oc_xxxxxxxxxxxxxxxxxx  # Step 8 拿的
```

**重要**：commando 的 `.gitignore` 已经覆盖了 `**/credentials/`——凭据**不会被 git track**。

---

## Step 10 · 试发一条 demo 卡片

```bash
cd /path/to/commando

# 先 dry-run 看会发什么
python tools/route.py --demo waiting

# OK 之后真发
python tools/route.py --demo waiting --apply
```

成功的话飞书里 bot DM 会即时收到那张 coral 卡片。

**4 个 demo 可选**：

```bash
python tools/route.py --demo im       # agent 主动找你
python tools/route.py --demo waiting  # 等你审稿
python tools/route.py --demo done     # 高价值任务完成
python tools/route.py --demo morning  # 日报式（选题已入库）
```

每个对应 `my-agent/event-routing.yaml` 里的一条 rule，飞书卡片会按对应 template 渲染。

---

## 常见问题

### `lark-cli` 报 "Permission Denied" 或 "Scope Not Granted"

- Step 3 的 scope 没批：回飞书开放平台 → 权限管理 → 查每一项状态是「已生效」
- Bot 版本没发布：回 Step 5
- 等 1 分钟后重试（飞书后台缓存）

### `chat_id` 抓不到

- bot 还没被你加到自己飞书里（Step 6）
- 你还没给 bot 发过消息（Step 7）
- `chats-list` 输出**没有 `p2p`**：再 DM bot 一条试试

### 卡片渲染奇怪 / 按钮不出来

- 飞书客户端版本太老（V2 卡片需要 7.0+）
- 升级 desktop / 移动端 App

### 我有多个 agent 怎么办

复用同一个 bot 即可——`bot_app.notify_chat_id` 不变，每个 agent 的 `event-routing.yaml` 各写各的规则、各自 push 到同一个 chat。这是 commando 的核心架构假设。

如果你想要 agent 分开发到不同 chat（比如阿土发个人 DM，财娃发投研群），在 `event-routing.yaml` 里加多个 destination，每个用不同 `notify_chat_id`。

---

## v0.2 会简化成

```bash
commando connect im-feishu
# → 引导走完上面 10 步，自动写 credentials.yaml + 抓 chat_id
```

但 v0.1 的手动流程是**让你完整理解一遍权限模型**——比一行命令的"黑魔法"
更适合 commando docs-first 的产品哲学。

---

## 安全提醒

- App Secret 等价于 bot 的 password —— 别截图发别人 / 别 commit
- `notify_chat_id` 泄了风险不大（只有 bot 才能往里发） —— 但也别公开
- 收到来自陌生人的卡片可疑链接 → 立刻在飞书举报 + 暂停 bot

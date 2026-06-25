<p align="center">
  <img src="dashboard/ant.svg" alt="commando" width="100" />
</p>

# commando

> **用 25 分钟，配出一个属于你自己的 AI 数字员工。** 跑在你已经在用的 AI 工具上——Claude Code、Cursor、Windsurf、Codex、Kimi、GLM、Qwen、豆包、MiniMax、Gemini 都行。

[← English README](README.md)

你花 25 分钟跟你的 AI 工具对话，它在磁盘上产出 `my-agent/` 目录——Charter（章程）+ Schedule（排班）+ Skills（技能）。系统的定时器跑这些 Skill，输出推到你已经在用的飞书 / Notion / IM 里。**这个数字员工是你拥有的文件**，不是租来的 SaaS。

```bash
curl -fsSL https://raw.githubusercontent.com/Frank-Pu/commando/main/install.sh | sh
commando onboard         # 25 分钟对话 → ./my-agent/
commando build-skills    # 填好每个 Skill 的 prompt body
commando go-live         # 接 IM + 装定时调度
```

第二天早上 8 点，你的数字员工开始跑第一个任务，飞书弹卡片找你审稿。

---

## 数字员工长什么样？

三个真实的 Configuration 例子，看完你就懂这个工具能干嘛：

### 1. 增长合伙人 — 独立产品创作者的内容 + 用户洞察搭档

> *Charter 节选：*"我是 [产品名] 的增长合伙人。风格：朴实、数据先行、不端着、绝不用营销腔。红线：AIGC 手改率 ≥ 20%、小红书外链零容忍、营销密度 ≤ 20%。"

> *Schedule：*`morning_sense 每天 08:00` · `xhs_draft 周二/周五 11:00` · `weekly_data_review 周五 16:00` · `weekly_reflection 周日 19:00`

*已经为 [LeMingle](https://lemingle.com) 持续服务 6+ 个月，本仓库的标准参考 Configuration。*

### 2. 理财顾问 — 始终在线的账户守望者

> *Charter 节选：*"我是你的私人理财顾问。红线：绝不替你做任何交易；绝不预测市场；绝不推荐高风险产品；季度报告必须包含一节'我可能错在哪'。"

> *Schedule：*`daily_portfolio_health 每天 07:00` · `monthly_tax_check 每月 1 日 09:00` · `quarterly_rebalance_review 每季度末`

### 3. 求职陪跑导师 — 跳槽 3 个月的高强度陪练

> *Charter 节选：*"我是你的跳槽教练。风格：温和但不放水。红线：绝不帮你写虚假履历；绝不替你回避真实弱点；3 个月内毫无进展我会直接告诉你。"

> *Schedule：*`daily_listing_scan 每天 09:00` · `interview_debrief 手动触发` · `weekly_pacing_check 周日 19:00`

---

## 为什么用 commando，不用别的？

|   | **commando** | ChatGPT / GPTs | LangChain / Agent 框架 | Zapier + LLM |
|---|---|---|---|---|
| 数字员工归你所有 | ✅ 文件在你的仓库里 | ❌ 锁在 OpenAI 上 | ✅ 代码在你仓库 | ❌ 锁在 Zapier 上 |
| 自由选 LLM | ✅ 任意（Claude / GLM / Kimi …）| ❌ 只能 OpenAI | ⚠️ 每换一家都改代码 | ⚠️ 只能用它的集成 |
| 用操作系统定时器调度 | ✅ launchd / systemd / cron | ❌ 不支持 | ⚠️ 自己写 | ✅（用它的 cron） |
| 输出推到你自己的工具 | ✅ 飞书 / Notion / IM | ❌ 只在 ChatGPT 里 | ⚠️ 自己接 | ✅（用它的集成） |
| 长期记忆可读可改 | ✅ markdown 文件在磁盘 | ⚠️ 藏在 context 里 | ⚠️ 自己接向量库 | ❌ 没有记忆 |
| 上手有引导 | ✅ 25 分钟对话产出 | ❌ 自己想 | ❌ 自己想 | ❌ 自己想 |

一句话：**Runtime 是商品，Configuration 是护城河**。我们故意不卷 Runtime，把全部精力放在让 Configuration 可分享、可版本化、归你所有。

---

## 怎么工作（你只需要记住这三层）

| 层 | 是什么 | 谁来管 |
|---|---|---|
| **Charter（章程）** | 数字员工的宪法——身份、风格、ICP、红线。每次调用自动注入。 | 你写的 `charter.md` |
| **Skills（技能）** | 离散的任务能力（写一篇笔记、复盘一场会议）。被 Schedule 或 IM 触发。 | `skills/*/SKILL.md` |
| **Schedule（排班）** | 决定什么时候触发哪个 Skill。自动翻译成 launchd / systemd。 | `schedule.yaml` |

随时找它聊天（"帮我想一下 X"）天然就能用，因为 Charter 永远在 context 里——不用专门写 Skill。

---

## 立刻装一个社区 Skill 试试

```bash
commando install @commando/daily-briefing      # 每日晨间简报
commando install @commando/meeting-debrief     # 会议 → action + Semantic 记忆
commando install @commando/competitive-watch   # 每周竞品 diff
commando install https://github.com/…/SKILL.md # 任意 GitHub URL 都行
```

Skill 装进来后会**根据你的 Charter 自动重 build**，让它的风格、ICP、红线和你的数字员工一致。

---

## 当前状态

**已有**：install + onboard + build-skills + go-live + schedule + 飞书 IM + 本地 dashboard + Registry（3 个已验证的通用 Skill）。经过 3 轮陌生人上手 dogfood 验证。

**未做**：Linux `systemd` 模板（目前只 macOS 的 launchd 跑通）、更多第三方 agent CLI 的实测命令格式、Stripe / Plausible KPI 看板。

---

## 贡献

最需要的贡献：

1. **你领域的真实 Configuration** — 财务、法务、运营、研究、客户成功。PR 一个 `examples/<角色>/`（脱敏的 charter + schedule）。
2. **Registry Skill** — 在 `registry/<skill-name>/SKILL.md` 加 + `skills.json` 加索引。
3. **验证第三方 CLI** — `commando/runtime/llm.py` 里的 `kimi` / `glm` / `qwen` / `doubao` / `gemini` 命令格式真跑通后 PR 改 verified 状态。

## License

[MIT](LICENSE) — Frank PU.

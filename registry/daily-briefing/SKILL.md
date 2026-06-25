---
name: daily-briefing
description: 每日晨间简报 — 扫一遍 episodic memory + connectors，5 行内输出"昨天发生了什么 / 今天要做什么 / 哪里需要你拍板"。
status: active
model: claude-opus-4-7
playbooks: []
tags: [daily, briefing, observability, universal]
capability_requirements:
  - Messaging.send_dm
license: MIT
license_url: https://github.com/Frank-Pu/commando/blob/main/LICENSE
adapts_to: universal
source_handle: "@commando/daily-briefing"
---

# /daily-briefing — 一份用户每天起床第一眼能看完的简报

## Identity anchor

You ARE the agent described in the Charter injected at the top of this context. Voice / red lines apply — speak in the agent's voice, not a generic system tone.

## Inputs

- 昨天 24 小时窗口的 episodic events（trigger / done / fail / im）— 从 `memory/episodic/<yesterday>.jsonl` 取
- 今天 schedule.yaml 里 `enabled: true` 的 cron tasks（按 `cron_time` 排序）
- 当前 connector 状态（IM 推送 / 文档协作 / 信息源 — 哪些可用）
- 可选：Charter §3 的北极星指标，如果用户已记录上周末值

## Process

1. **盘点昨天发生了什么**（≤ 2 行）
   - 用 episodic events 统计：跑了 N 个 task，M 个 done，K 个 waiting，F 个 fail
   - 如有 fail，**点名是哪个 skill** + 失败时间
   - 如有 waiting，告诉用户**有多少待审稿**（这是用户起床后第一关注的事）

2. **列出今天会自动发生的事**（≤ 3 行）
   - schedule.yaml 里今天会触发的 cron task，按时间排序
   - 每条一行：`HH:MM  task_id  → 输出到哪`
   - 如果 task 有 `requires_human_approval: true`，标记 ⚠️ 提醒用户届时要审稿

3. **判断是否需要人类介入**（最关键的一行）
   - 如果 connectors 缺关键的（如 IM 推送），告诉用户"今天的卡片会落到 ./workbench/ 等你手动拉"
   - 如果昨天有连续 ≥ 2 次某 skill fail，**前置阻塞**："建议先 debug X skill 再让它继续跑"
   - 如果没问题：一行温和的确认"今天预期会顺利运行，下次审稿在 HH:MM"

4. **可选的北极星速报**
   - 如 Charter §3 有 NSM 且能查到上周末值（Stripe / Plausible 接好），给个对比数字
   - 不能查到就别强行编（Charter §6 红线第 1 条：不假装爆款）

## Output

写一个**结构固定的 5 行简报**到 episodic + IM card：

```
🌅 早 [用户名]，昨天 [N done] · [M waiting] · [F fail]
今天预定：[HH:MM task] · [HH:MM task] · [HH:MM task]
⚠️ 待你审稿：[N 个]，在 [Workbench 路径 / IM 卡片]
🎯 NSM 上周末 [X]，本周目标 [Y] —— [距离 Δ]
[一句温度感的结尾，按 Charter 的 voice]
```

如果没有 IM 推送 connector，输出落到 `./workbench/daily-briefing-<date>.md`，并在 episodic 写 event 提示用户。

## Voice / quality gates

- **按 Charter §<voice section> 的语调**——不要用系统报告腔（"已完成扫描，发现…"），要像同事说话
- **数字优先于形容词**：写"3 个待审稿"不写"几个待审稿"
- **失败不掩饰**：fail 的 task 必须点名 + 时间，按 Charter §<红线> 的诚实原则
- **不超过 5 行**：用户睁眼第一秒就看完，超过 5 行 = 失败
- **温度感不端着**：结尾的一句话要让用户感觉是被关心，不是被汇报（Charter §<voice> 的"朴实不端着"原则）

## If Connectors Available

If **IM 推送** is connected:
- 简报作为 IM card 推送到用户的首选 IM（飞书 / 钉钉 / Slack / Discord），8:00 起床档刚好

If **文档协作** is connected:
- 简报同时归档到协作平台的"晨间简报"页面，方便用户日后翻看周度模式

If no connectors available:
- 输出到 `./workbench/daily-briefing-<YYYY-MM-DD>.md`，附 episodic event 提示用户位置（默认行为）

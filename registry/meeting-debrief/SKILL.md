---
name: meeting-debrief
description: 会议复盘 — 把会议笔记（任意格式）提炼成"3 个结论 / N 个 action items / 给 Semantic 的 insights"，自动按主人留 follow-up。
status: active
model: claude-opus-4-7
playbooks: []
tags: [meeting, debrief, semantic-memory, universal]
capability_requirements:
  - Documents.create
license: MIT
license_url: https://github.com/Frank-Pu/commando/blob/main/LICENSE
adapts_to: universal
source_handle: "@commando/meeting-debrief"
---

# /meeting-debrief — 把一段对话凝结成可执行 action items + 长期沉淀

## Identity anchor

You ARE the agent described in the Charter injected at the top of this context. Voice + red lines apply — particularly Charter §<voice section> on 不端着 + Charter §<红线> 上 ICP / 边界。

## Inputs

- `notes`: 用户提供的原始会议笔记（飞书妙记 / Notion / 飞书文档 / 口述转写 / 任意 markdown）
- `participants`: 参会人姓名 + 角色（用户提供 or 从笔记里抽）
- `meeting_type`: 用户访谈 / 客户对接 / 团队站会 / 投资人沟通 / 其他（用户标 or 从内容推断）
- Charter context：当前 agent 的 ICP / 关键红线 / 北极星指标——会议内容里凡是相关的都要 cross-ref

## Process

1. **判断会议类型 + 选模板**
   - If `meeting_type == "用户访谈"` → 走 ICP 校准 + user-quote-vault 提取模板
   - If `meeting_type == "客户对接"` → 走需求 + 红线对照 + 合规检查模板
   - If `meeting_type == "团队站会"` → 走 blocker 提取 + Action Items 模板（更轻）
   - If `meeting_type == "投资人沟通"` → 走 metric 对账 + Q&A 沉淀模板
   - Else → 通用 debrief 模板（3 结论 + N action + insights）

2. **提取 3 个核心结论**（不超过 3 个，超过就是 noise）
   - 按 **Charter §<北极星 / ICP / 红线>** 关联度排序，最相关的写第一条
   - 每条 ≤ 30 字，**用对方原话**而不是你的概括（Charter §<voice>：用户的词比你的好）
   - 如某结论挑战了 Charter 的当前判断，**显式标 ⚠️ "这条挑战了 Charter §X"**——为 Re-onboarding 攒证据

3. **拆 Action Items**
   - 格式：`[ ] @负责人 — 具体动作 — due <date>`
   - 没有明确 owner 的 → 标 `@unassigned`，让用户拍板
   - 没有明确 due 的 → 标 `due TBD`，**不要瞎填日期**
   - 优先级用 `[P0]` `[P1]` `[P2]` 三档，按用户判断或 Charter §<北极星> 推断

4. **抽 Semantic Memory 的 insights**
   - 用户访谈类：抓 user-quote-vault 候选——原话 + 出处 + 时间戳
   - 客户对接类：抓 ICP 校准信号（"客户实际买单理由 vs 我们假设的差距"）
   - 通用：抓"和 Charter 当前假设不一致"的事实——这些是 Re-onboarding 的种子

5. **写 follow-up 给参会方**
   - 如果会议有外部参会者（用户 / 客户 / 投资人），按 **Charter §<voice>** 起草一封 follow-up
   - 包含：感谢 / 我们听到的 / 我们接下来会做的 / 时间承诺
   - **不要用模板化的客套**——按 Charter 风格写

## Output

落地三份文件 + 一个 IM card：

1. **`./workbench/meeting-debrief/<YYYY-MM-DD>-<participant>.md`** — 完整 debrief（结论 + actions + insights + follow-up draft）
2. **追加到 `./memory/semantic/user-quotes.md`**（如果是用户访谈类）— 用户原话 + 出处 + 关联 ICP 维度
3. **追加到 `./memory/semantic/icp-evolution.md`**（如果有 ICP 信号）— 这次访谈对 ICP 假设的支撑 / 反驳
4. **IM card**（如果 IM 推送 connector 可用）— 5 行精简版给用户审稿："3 结论 / N actions / 待你确认 follow-up"

## Voice / quality gates

- **结论用对方原话**：不要把"我们觉得文案太硬"翻译成"用户对 brand tone 有反馈"。原话保真度是 Semantic Memory 的核心价值（Charter §<voice>）
- **不超过 3 个结论**：超过 = 没有真正提炼。逼自己合并或砍
- **Action 必须 SMART**：Specific + Measurable + Assignable + Realistic + Time-bound——任何一项缺，标 `?` 让用户补
- **不替用户拍板**：拿不准的 owner / 优先级 / due，标 TBD / @unassigned 让用户确认，不要瞎猜
- **挑战 Charter 的内容必须显式标记**：⚠️ "这条挑战了 Charter §X" —— 这是 Re-onboarding 的种子，淹没在普通结论里就废了
- **Follow-up 用 Charter §<voice>**：朴实 vs 客套，按 agent 风格

## If Connectors Available

If **IM 推送** is connected:
- 5 行精简 debrief 推 IM card 给用户审稿，按钮跳完整 markdown

If **文档协作** is connected:
- 完整 debrief 自动归档到协作平台（飞书 wiki / Notion / Confluence）的"会议笔记"section
- Follow-up 起草到协作平台的草稿区，等用户审完后发出

If **结构化记录** is connected:
- Action Items 自动建在协作平台的任务库（Linear / Notion DB / 飞书任务）

If no connectors available:
- 全部输出到 `./workbench/meeting-debrief/` 本地目录（默认行为），用户手动同步

---
name: competitive-watch
description: 竞品追踪 — 每周扫一遍 N 个竞品（产品页 / changelog / 社媒 / 公关稿），输出 "他们做了什么 / 对我们的影响 / 我们要不要回应"。
status: active
model: claude-opus-4-7
playbooks: []
tags: [competitive, weekly, market-watch, universal]
capability_requirements:
  - WebSearch
  - Documents.create
license: MIT
license_url: https://github.com/Frank-Pu/commando/blob/main/LICENSE
adapts_to: universal
source_handle: "@commando/competitive-watch"
---

# /competitive-watch — 让 Charter 永远知道竞品在干什么

## Identity anchor

You ARE the agent described in the Charter injected at the top of this context. Voice + red lines apply — 特别 Charter §<北极星 / ICP> 决定了什么变化"对我们有影响"。

## Inputs

- `competitors`: Charter 或 schedule.yaml 里维护的竞品列表，每个含：name / official_url / changelog_url? / social_handles? / pricing_url?
- `window`: 扫描时间窗（默认上周 = 7 天）
- `last_run_snapshot`: 上次跑的快照（存 `./memory/semantic/competitive-snapshots/<date>.md`），用来 diff
- Charter §<ICP / 北极星 / 红线>：决定每条变化的相关度评分

## Process

1. **逐个竞品扫描**（一定 WebSearch / WebFetch，不要凭印象）
   - 官方产品页：抓首屏 hero + 核心价值主张文字
   - 价格页：抓套餐结构 + 价格数字
   - Changelog / blog（如有）：抓时间窗内的发布
   - 主要社媒账号（如已知 handle）：抓时间窗内有大互动的帖子
   - **不要瞎编**：抓不到内容就标"抓取失败/无访问权限"，不要补脑

2. **和上次快照做 diff**
   - 价格变了？hero 文案变了？发了大功能？社媒声量异常？
   - **只汇报真实变化**——没变化的竞品一行带过："X 这周无明显变化"
   - 变化项标 `[NEW]` / `[CHANGED]` / `[REMOVED]`

3. **按相关度评分**（每条变化 0-3 分）
   - **3 分**：直接触及我们的 ICP 或核心功能差异化（Charter §<ICP / 差异化>）
   - **2 分**：触及我们的渠道 / 定价 / 营销策略
   - **1 分**：方向相关但不构成直接威胁
   - **0 分**：noise（如换 logo、季节 marketing）—— **不写入正文**，只在末尾 stats 提

4. **判断我们要不要回应**（最难的一步，按 Charter §<北极星> 优先级）
   - 高分变化的每一条都要回答：**"我们要不要回应？回应什么？什么时候？"**
   - 三种态度只能选一：
     - `[跟进]` — 我们也做（要给一个时间窗）
     - `[观察]` — 暂不做，下次扫看是否升级
     - `[反向定位]` — 我们故意不做，因为 Charter §<差异化> 决定了我们走另一条路
   - **不要"我们再讨论一下"** —— 这是空话。逼自己拍 1/3

5. **存快照 + 更 Semantic**
   - 这次的完整快照存 `./memory/semantic/competitive-snapshots/<YYYY-WW>.md`，下周作为 diff 基线
   - 高分变化 + 我们的应对决议追加到 `./memory/semantic/competitive-decisions.md`——这是长期沉淀，跨季度看竞品演化的事实库

## Output

输出一份 **markdown 报告**到 `./workbench/competitive-watch/<YYYY-WW>.md`：

```markdown
# 竞品观察 · YYYY 第 N 周

## 概览
- 扫了 X 个竞品 · 发现 Y 项变化 · Z 项需我们决策

## 高优先级变化（需要决策）
### 竞品 A · [NEW] 上线了 X 功能
- 原话/截图：「...」
- 相关度：3/3（直击我们 §2.2 ICP）
- 决议：[跟进 | 观察 | 反向定位] — <理由 1-2 句>
- 时间窗：<如跟进，给具体 by-date>

### 竞品 B · [CHANGED] 价格从 $X → $Y
- ...

## 中低优先级（仅作记录）
- 竞品 C · 换了 hero 文案 (1/3，本周观察)
- 竞品 D · 无明显变化

## 给 Semantic 的沉淀
- <对 ICP 假设的支撑/反驳>
- <对差异化判断的支撑/反驳>
```

## Voice / quality gates

- **抓不到就说抓不到**：宁可写"X 的 changelog 抓取失败"也不要编内容（Charter §<红线> 的诚实原则）
- **只汇报真实变化**：竞品这周啥也没干就一行带过，**不要为了凑长度写"持续运营中"这种水话**
- **每条高分变化必须有 owned decision**：跟进 / 观察 / 反向定位 三选一，不留"待讨论"
- **diff 不用形容词，用事实**：写"价格从 $29 → $39 (+34%)"不写"价格大幅上调"
- **按 Charter §<北极星> 评分**：相关度判断不能凭直觉，要 cross-ref Charter 里写明的 ICP / 差异化
- **不超过 1 页**：超过 = 没在过滤。逼自己砍

## If Connectors Available

If **IM 推送** is connected:
- 5 行精简版（"扫了 X · 发现 Y · 需要你拍板 Z 个"）推 IM card，按钮跳完整报告

If **文档协作** is connected:
- 完整报告 + 历次快照归档到协作平台的"竞品观察"目录，方便季度回看趋势

If **结构化记录** is connected:
- 高优先级变化 + 我们的决议自动入"竞品决议库"（任务 / DB），按 status 追踪执行

If no connectors available:
- 全部输出到 `./workbench/competitive-watch/` 本地（默认行为），用户手动同步

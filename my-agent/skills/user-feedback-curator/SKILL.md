---
name: user-feedback-curator
description: 把 IM/邮件/小红书评论/支付后台备注里收集到的用户反馈和原话，按主题分类沉淀到 Semantic Memory
status: draft
playbooks: [growth-partner]
capability_requirements:
  - Messaging.send_dm
  - Documents.update
---

# /user-feedback-curator (DRAFT)

> ⚠️ status: draft — 等工程实现 body 后改 status: active。

## 为什么这个 Skill 关键（pre-PMF 阶段）

用户 A 案例证明：**用户原话 → 产品迭代**是当前最高 ROI 的循环。但用户原话散落在多个渠道（IM / 邮件 / 小红书评论 / 支付后台备注），容易丢。这个 Skill 的工作是**永远不让用户 A "某个核心功能"那种话丢失**。

## 输入契约

```python
{
  "sources": ["feishu_im", "feishu_mail", "xhs_comments", "stripe_notes"],
  "since": "<last_run_ts>"
}
```

## 工作步骤（草稿）

1. 从所有 source 抓自上次运行以来的新条目
2. 过滤出**用户原话**（带情绪 / 带具体功能 / 带场景的句子，不是"好用！"这种空话）
3. LLM 分类到现有 Semantic Memory 主题：
   - `user-quote-vault.md`（所有原话）
   - `feature-requests.md`（功能建议）
   - `pain-points.md`（痛点）
   - `ICP-signals.md`（ICP 画像验证 / 反驳的信号）
   - 找不到主题 → 新建 draft 主题
4. 追加到对应 markdown 文件，**带证据来源**（IM 链接 / 邮件 thread ID / 小红书评论 URL）
5. 周报里 highlight 本周新增的 5 条最有信号 quote

## 输出契约

更新 `my-agent/memory/semantic/*.md` 对应主题文档（status: active 的不动，新条目 append；status: draft 的等 Qihang review）。

## 红线

- **用户隐私**：用户原话存储前匿名化（去名字 / 去公司 / 去精确地理）
- **数据真实**：不杜撰用户原话——找不到来源的不写

## 失败回退

抓取失败 → 仅记录本次 trigger 失败，下次重试。不阻塞下游任务。

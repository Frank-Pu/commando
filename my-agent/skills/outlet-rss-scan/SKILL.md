---
name: outlet-rss-scan
description: 每日扫外刊 RSS（Economist / Atlantic / NYT / New Yorker / Aeon 等），提取地道表达密度高的片段进选题池
status: draft
playbooks: [growth-partner]
capability_requirements:
  - ContentSource.list_posts
  - StructuredData.create_record
---

# /outlet-rss-scan (DRAFT)

> ⚠️ status: draft — Runtime 不会自动跑 draft skill。等你工程实现 body 后改 status: active。

## 输入契约

```python
{
  "rss_feeds": ["https://...", ...],          # 来自 connectors.yaml 的 outlet_rss source
  "max_per_feed": 5,
  "time_window": "24h"
}
```

## 工作步骤（草稿）

1. 拉每个 feed 最新 N 篇文章（用 `connectors.outlet_rss.list_posts`）
2. 用 trafilatura 类工具提取正文（atu 已有现成实现可参考）
3. **打分维度**（基于 Charter 5 的内容公式 A/B/C）：
   - **idiom_density**：文章中地道搭配的密度
   - **ICP_resonance**：是否触及海外华人专业人士的工作场景
   - **formula_fit**：适合做哪个公式（A / B / C）
   - **red_line_safe**：是否避开了 Charter 7 的禁区
4. score >= 4 的片段写入选题池 bitable

## 输出契约

写入飞书 bitable 选题池，每条 record 字段：

```
{
  "source_outlet": "The Economist",
  "article_url": "...",
  "excerpt": "...",          # 关键片段
  "idiom_density": 4.3,
  "ICP_resonance": 4.5,
  "formula_hint": "A",       # 推荐用哪个公式
  "status": "Inbox"
}
```

## 红线

继承 Charter 7 全局红线。本 skill 特有：
- 不抓付费墙后文章（合规）
- 不全文搬运，只摘关键片段（合规 + 版权）

## 失败回退

任一 feed 抓取失败 → 跳过该 feed，其他正常；全部失败 → workbench status: Blocked + IM 通知 Qihang。

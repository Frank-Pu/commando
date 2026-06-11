---
name: marketing-kit
description: 8 件套通用营销 Skill bundle（营销文案 / 效果分析 / 竞品追踪 / 社媒热点 / 广告合规 / 品牌调性 / SEO 内容优化 / 活动策划）
source: "@frank-pu/marketing-kit@planned"
status: imported-placeholder
playbooks: [growth-partner]
---

# /marketing-kit （bundle）

由 commando 在 Onboarding 阶段从 Skill Registry 占位导入。

**bundle 内容**：
- 营销文案（marketing-copy）
- 营销效果分析（marketing-effect-analysis）  ← schedule.yaml 调用
- 竞品追踪（competitor-tracking）
- 社媒热点追踪（trending-scan）
- 广告合规检查（compliance-check）
- 品牌调性审查（tone-review）
- SEO 内容优化（SEO-content-optimization） ← schedule.yaml 调用
- 活动策划（campaign-planning，储备）

**实际实现待**：
- commando CLI 上线后跑 `commando install @frank-pu/marketing-kit`，或
- 从 [atu 仓库 configuration/skills/](https://github.com/Frank-Pu/atu/tree/main/configuration/skills) 手动 fetch 每个 sub-skill

**本配置启用的 sub-skills**：
- ✅ marketing-effect-analysis（周度数据复盘）
- ✅ SEO-content-optimization（月度知乎长文）
- ⏳ 其余作为储备，按需启用

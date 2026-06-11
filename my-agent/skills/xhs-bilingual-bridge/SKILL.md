---
name: xhs-bilingual-bridge
description: 把 Reddit/HN 优质讨论加工成小红书 Bilingual Bridge 图文，输出 markdown 摘要 + JSON slide_plan 双协议
source: "@frank-pu/xhs-bilingual-bridge@planned"
status: imported-placeholder
playbooks: [growth-partner]
capability_requirements:
  - Documents.create
  - Documents.update
  - Storage.upload
  - Messaging.send_dm
requires_human_approval: true
---

# /xhs-bilingual-bridge

由 commando 在 Onboarding 阶段从 Skill Registry 占位导入。

**实际实现待**：
- commando CLI 上线后跑 `commando install @frank-pu/xhs-bilingual-bridge`，或
- 从 [atu 仓库 configuration/skills/xhs-bilingual-bridge/](https://github.com/Frank-Pu/atu/tree/main/configuration/skills/xhs-bilingual-bridge) 手动 fetch

**本配置的关键 input 提示**（自动注入 from Charter 5.0）：
- 内容公式配比：A (ICP-Bridge) 50% / B (用户案例放大) 30% / C (PLG) 20%
- ICP：海外华人专业人士（不再泛"留学生/备考生"）
- 营销密度：小红书 1/10 笔记直接提产品名

**红线**（自动注入 from Charter 7.x）：见 AI 痕迹清洗清单 + 数据真实性 + 复刻边界。

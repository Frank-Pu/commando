---
name: reddit-source-mining
description: 扫指定 subreddit 拉 top 候选帖 + LLM 4 维打分（ICP / 钩子 / 红线 / 多样性）→ 写入选题池
source: "@frank-pu/reddit-source-mining@planned"
status: imported-placeholder
playbooks: [growth-partner]
capability_requirements:
  - ContentSource.list_posts
  - ContentSource.get_comments
  - StructuredData.create_record
---

# /reddit-source-mining

由 commando 在 Onboarding 阶段从 Skill Registry 占位导入。

**实际实现待**：
- commando CLI 上线后跑 `commando install @frank-pu/reddit-source-mining`，或
- 从 [atu 仓库 configuration/skills/reddit-source-mining/](https://github.com/Frank-Pu/atu/tree/main/configuration/skills/reddit-source-mining) 手动 fetch 内容到此目录

**功能预期**：见 atu 原版 SKILL.md。本占位文件只为让 commando Runtime 加载 Configuration 时不报错。

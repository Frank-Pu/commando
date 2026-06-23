---
name: daily-greeting
description: Write a one-line greeting in the agent's voice based on Charter section 1.
status: active
model: claude-opus-4-7
playbooks: []
capability_requirements:
  - Messaging.send_dm
---

# /daily-greeting — a runnable v0.2 sample Skill

You ARE the agent described in the Charter injected at the top of this context.

Write ONE sentence — under 30 Chinese characters — that:
1. Greets the user in the agent's voice (use the agent's 风格 / 沟通方式 from Charter §1)
2. Mentions one specific thing about today's plan or what you noticed overnight (
   you may invent something plausible based on the agent's role)
3. Ends with a tiny prompt to engage (a question, a "我先去 X" hint, etc.)

Output: just the one sentence. **No preamble, no quotes, no markdown.**

Examples (for an indie product growth agent):
  早，昨晚扫了 r/languagelearning，挑了 3 条选题，咱们晨会聊？
  来啦 Qihang，今天周二 11:00 我会产小红书初稿，记得审稿。

Examples (for a finance research agent):
  开盘前 brief 在路上了，BYD 财报今晚出，先帮你看哪几个数？

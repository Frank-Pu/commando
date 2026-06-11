# Skill — commando 的能力单元

> commando Skill = **Claude Code Skill 格式 + commando frontmatter 扩展**。
> 不发明新格式——直接复用社区事实标准，让 Claude Code 用户能把现成
> Skill 带进 commando，也能把 commando 写的 Skill 拿回 Claude Code 单用。

## 一句话理解

Skill = **一份结构化、循环性、状态机化任务的陈述式说明书**。它告诉
LLM "这种活该怎么干"，不告诉它"什么时候干"（那是 Schedule 的事）。

**Skill 只用于 structured work**。用户和数字员工 ad-hoc 聊产品/灵感**不
需要 Skill**——那是 Charter context + LLM base 能力的事，详见
[`SKILL.md`](../skills/onboarding/SKILL.md) 的"心智模型"章节。

## 文件位置

```
my-agent/
└── skills/
    ├── <skill-name-1>/
    │   ├── SKILL.md              ← 必有
    │   ├── examples.md           ← 推荐：few-shot 标杆
    │   ├── templates/            ← 推荐：渲染模板等
    │   └── ...                   ← 任意辅助文件
    └── <skill-name-2>/
        └── SKILL.md
```

## SKILL.md frontmatter

### 标准 Claude Code 字段（必有）

```yaml
---
name: xhs-bilingual-bridge
description: >
  把 Reddit/HN 优质讨论加工成小红书 Bilingual Bridge 图文笔记，
  输出 markdown 摘要 + JSON slide_plan 双协议。
model: claude-sonnet-4-6      # 不写则用 Configuration 默认
allowed_tools: [Read, Write, WebFetch]
---
```

### commando 扩展字段（可选，但有用）

```yaml
---
# ...标准字段省略
source: "@frank-pu/xhs-bilingual-bridge@0.3"   # 从 Skill Registry 导入时填
status: draft | active | deprecated            # 默认 active
playbooks: [growth-partner]                    # 哪些 playbook 推荐这个 skill
capability_requirements:                       # 需要 backend 提供哪些能力域
  - Documents.create
  - Documents.update
  - Messaging.send
requires_human_approval: true                  # 输出对外可见 → 必经审稿
---
```

**字段语义**：

- `source` — 当此 skill 通过 Registry 导入时，记录原始 `@author/name@version`。
  Configuration 里出现 `source` 表示"这是引用，不是用户原创"。
- `status: draft` — Onboarding 在 Confirmation 阶段产出的占位 skill 默认
  draft，Runtime 不会自动跑 draft skill（防止半成品上线）。
- `playbooks` — Skill Registry 检索时按这个字段反查"这个角色该装哪些 skill"。
- `capability_requirements` — Runtime 加载时校验当前 backend 是否提供这些
  能力；不满足直接报错"换 backend 或换 skill"。详见 commando 的
  Capability 词典（待写）。
- `requires_human_approval` — 触发时强制走 IM 审稿卡片才能继续。

## SKILL.md body 应该包含

按 atu 验证下来的模板：

```markdown
# /<skill-name> — <一句话定位>

<一段话：这个 skill 在 Charter 的哪个上下文里工作，承担什么角色>

## 输入契约

<明确说 task.inputs 长什么样，给一个 JSON 例子>

## <核心步骤 / 评分维度 / 公式>

<这里是 skill 的"知识本体"——LLM 看这段决定怎么干活>

## 输出契约

<明确说要写到哪里、什么格式。如 "落 samples/xhs_artifacts/<id>/
slide_plan.json"，或 "返回 markdown 摘要 + JSON 代码块双协议">

## 红线

<必须遵守的硬约束。Charter 的全局红线之上的 skill-local 红线>

## 失败回退

<出错时怎么办：写 Blocked 状态 / 推 IM / 重试 N 次等>
```

## commando 自己出厂的 Skill vs 用户 Configuration 里的 Skill

| 类型 | 路径 | 例子 |
|---|---|---|
| **commando 出厂 skill** | `commando/skills/<name>/SKILL.md` | `/onboarding`（旗舰），未来可能加 `/reonboard`、`/connect-wizard` |
| **用户 Configuration skill** | `my-agent/skills/<name>/SKILL.md` | `xhs-bilingual-bridge`、`reddit-source-mining` 等 |

两者格式完全一样。区别只在执行语境：commando 出厂 skill 在 commando CLI
任何时候都能调用；Configuration skill 只在那个 Configuration 加载后可用。

## Skill Registry

[`skills.json`](../skills.json) 是社区 Skill 索引。Onboarding 在 Calibration
阶段查询它，向用户推荐已有 Skill 而不是重写。

Registry 条目最简结构：

```json
{
  "id": "frank-pu/xhs-bilingual-bridge",
  "title": "小红书 Bilingual Bridge 图文 Skill",
  "summary": "...",
  "playbooks": ["growth-partner"],
  "tags": ["xiaohongshu", "content"],
  "status": "planned | released | deprecated",
  "source_url": "https://github.com/.../skills/xhs-bilingual-bridge"
}
```

发新 Skill 只需要给 [`skills.json`](../skills.json) 发 PR 加一条——
Day 1 不维护中心化注册服务器。

## Skill 之间怎么通信

**不要直接互调**。commando 沿用 atu 的 blackboard 架构：
- Skill A 把产物写到 Workbench 某行
- Skill B 由 Workbench 状态变化（chain trigger）触发 → 读那行 → 加工
- 中间路径完全在 Workbench 上可见，便于人审

## Skill 的演化路径

1. **诞生**：Onboarding 写 draft 占位（`status: draft`）
2. **首次实施**：用户/agent 把 body 写完整，去掉 `status: draft`
3. **校准**：Reflection 周期发现这个 skill 表现差 → 在 Episodic Memory
   写"建议改 SKILL.md 第 X 段"→ 用户决定是否采纳
4. **抽出 Registry**：用得好的 Skill 抽走 Configuration-specific 内容，
   PR 到主仓 `skills.json`
5. **被引用**：他人 Configuration 通过 `source: @author/name` 导入

## 反模式（贡献 Skill 时常见的）

- ❌ 把 Charter 内容（身份/红线/北极星）抄进 Skill body —— 重复且不一致
- ❌ Skill 内硬编码具体平台 API 调用 —— 应通过 `capability_requirements`
  + backend driver
- ❌ "万能型" Skill（一个 skill 干 5 件事）—— 拆 5 个，靠 chain trigger 串
- ❌ Skill 直接发布对外产物 —— 必须经 `requires_human_approval` 卡片
- ❌ Skill body 写"如果用户问 X 你就回答 Y"—— ad-hoc 对话不需要 skill

---

*Skill 是 commando 里最容易写错的产物——因为格式自由度大，新手会把
Charter / 业务逻辑 / 数据 / 红线全往 SKILL.md 里塞。写之前对照本文档
的"反模式"自查一遍。*

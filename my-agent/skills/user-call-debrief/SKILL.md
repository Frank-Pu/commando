---
name: user-call-debrief
description: 用户访谈后 debrief — 把 Qihang 口述/笔记的访谈内容提炼成 insights，进 Semantic Memory
status: draft
playbooks: [growth-partner]
capability_requirements:
  - Documents.create
  - Documents.update
---

# /user-call-debrief (DRAFT)

> ⚠️ status: draft — 等工程实现 body 后改 status: active。

## 触发方式

Qihang 通过 IM 触发："刚跟 X 聊完，这是我笔记 / 录音 transcript"。

## 输入契约

```python
{
  "user_identifier": "...",
  "call_notes": "...",                # Qihang 的笔记 / transcript
  "call_duration_min": int,
  "linked_prep_doc": "<docx ref>"     # 可选：本次 prep 文档
}
```

## 工作步骤（草稿）

1. **提炼 insights**（不超过 5 条，每条≤2 句）：
   - 用户原话（值得永久存档的）
   - 已验证的 ICP 信号
   - 推翻 ICP 的反信号
   - 功能 / 体验改进建议
   - 推广 / 留存机会
2. **分类落 Semantic Memory**：
   - 用户原话 → `semantic/user-quote-vault.md`（draft 状态等 Qihang promote）
   - 功能建议 → `semantic/feature-requests.md`
   - ICP 验证/反驳 → `semantic/icp-refinements.md`
   - 失败模式 → `semantic/what-doesnt-work.md`
3. **行动项**：
   - 提出 1-3 个 next-action（如"把这位用户加入 closed beta 邮件列表"）
   - 但不替 Qihang 做决策——仅建议
4. **回环 prep doc**：
   - 如果有 linked_prep_doc，对照"我们准备问的 vs 实际聊到的"差距，写进 debrief

## 输出契约

落地一份飞书 docx：`call-debrief-<user>-<date>.md`，结构：

```
# Call Debrief: <user> · <date>

## 5 条 insights
1. ...

## 用户原话（已进 Semantic Vault）
> ...
> ...

## ICP 信号
- ✅ 已验证：...
- ⚠️ 反信号：...

## 功能 / 体验建议（已进 Semantic Feature Requests）
- ...

## 建议 next-actions
- ...

## 与 prep 的差距
- 我们准备问 X，实际没问到
- 用户主动提到 Y，prep 里没料到
```

更新 Semantic Memory 对应主题文件。推 IM 卡片提醒 Qihang："Debrief 好了，5 条 insights 待你 review"。

## 红线

- **用户隐私**：原话存储匿名化（除非明确征得用户同意）
- **数据真实**：不杜撰、不修饰 insights——Qihang 没说过的不写

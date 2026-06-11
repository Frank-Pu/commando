---
name: user-call-prep
description: 用户访谈前 prep — 读对方 LinkedIn / 历史交互 / Semantic Memory，起草 5 个问题
status: draft
playbooks: [growth-partner]
capability_requirements:
  - WebFetch
  - Documents.create
  - Messaging.send_dm
---

# /user-call-prep (DRAFT)

> ⚠️ status: draft — 等工程实现 body 后改 status: active。

## 触发方式

Qihang 通过 IM 触发："我明天要和 X 聊 / 跟 Y 视频"。

## 输入契约

```python
{
  "user_identifier": "...",          # 邮箱 / 姓名 / 小红书 ID / LinkedIn URL
  "context_hint": "...",             # 可选：Qihang 写的"对方提了 X 想聊"
}
```

## 工作步骤（草稿）

1. **身份识别**：从 identifier 找到对方在系统里所有相关记录
   - 历史 IM 对话（如果有）
   - 支付后台付费记录（如果有）
   - 小红书互动记录（如果有）
   - LinkedIn URL（如果有）→ WebFetch 抓公开 profile
2. **背景整合**：
   - 对方所在职业 + 行业（关键：Charter 3 ICP 是否命中）
   - 对方已知的产品反馈
   - 对方使用 LeMingle 的活跃度
3. **目标 alignment**：
   - 如果是 paid user → 重点问"留存动力 / 还缺什么 / 推荐人意愿"
   - 如果是免费用户 → 重点问"为什么没付 / 替代方案 / 触发付费的条件"
   - 如果是新接触 → 重点问"如何发现我们 / 第一印象"
4. **起草 5 问**（不超过 5 个，按重要性排序）：
   - 1 个核心痛点确认
   - 1 个使用细节挖掘
   - 1 个 ICP 验证
   - 1 个产品改进信号
   - 1 个推广 / 留存信号

## 输出契约

落地一份飞书 docx：`call-prep-<user>-<date>.md`，结构：

```
# Call Prep: <user> · <date>

## 对方画像
...

## 历史交互摘要
...

## 本次 5 问（按推荐顺序）
1. ...
2. ...
...

## 我建议你录音 / 不录音
（基于敏感性判断）
```

推 IM 卡片提醒 Qihang：「Call prep 好了，建议先扫一眼这份 doc 再去 call」

## 红线

- **用户隐私**：不抓 LinkedIn / 公开渠道之外的 PII
- 不假装是 Qihang 本人写的——doc 头明确标"by 阿土"

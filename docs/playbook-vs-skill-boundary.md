# Playbook 和 SKILL.md 的内容边界

> **核心原则**：写 playbook 时，先问自己——这条建议是关于「commando 怎么
> 工作」，还是关于「这个角色具体怎么干」？
> **前者 → 改 [`skills/onboarding/SKILL.md`](../skills/onboarding/SKILL.md)**
> **后者 → 才放 [`playbooks/<role>.md`](../playbooks/)**

这是 commando 仓库里**最重要的一条 contributor 原则**——写错了不会立刻
出 bug，但会让每份新 playbook 重复同样的 commando 通用内容，最终让仓库
变成"每份 playbook 都自带半本 commando 用户手册"的状态。

---

## 为什么这条边界必须早早立住

playbook 是给"领域先验"加载用的——它在 Onboarding 的 Discovery / Calibration
阶段被读进 LLM context，让对话有"我懂你的领域"的质感。

但 LLM 已经知道 commando 怎么工作（SKILL.md 已经注入了）。如果 playbook 又
把 commando 的工作机制重抄一遍：

- **token 成本上升**：同样的话每个 playbook 抄一遍
- **演化失同步**：commando 通用机制改了，所有 playbook 都要追改
- **错抄风险**：第二个写 playbook 的人凭印象抄，抄错了 commando 行为
- **抽象层级混淆**：用户读 playbook 时分不清"这是 commando 怎么样"还是
  "这个角色怎么样"

---

## 区分的两个问题

对每一条你想写进 playbook 的内容，问这两个问题：

### 问题 1：换一个角色，这条建议还成立吗？

| 答案 | 归属 |
|---|---|
| **成立**（财务分析师 / 客服 / 投研也都适用） | 改 SKILL.md，不要进 playbook |
| **不成立**（只对当前角色有效） | playbook |

### 问题 2：这条是说"commando 提供什么机制"，还是说"这个角色用机制做什么"？

| 答案 | 归属 |
|---|---|
| **机制本身**（如"ad-hoc 对话默认全开"） | SKILL.md / commando docs |
| **机制的具体使用**（如"增长合伙人 Charter 应该包含 ICP 字段"）| playbook |

两个问题任意一个指向 SKILL.md，就不要往 playbook 塞。

---

## 一个真实案例（来自 Onboarding skill 自己的测试）

**背景**：第一个 Onboarding 测试跑到 Phase 0，用户提出"我希望数字员工
能跟我探讨增长方向和产品迭代功能点"。

**当时的（错误）反应**：Onboarding skill 准备在 growth-partner playbook
里新增一个决议「Charter 上下文密度」，并新增一个心智模型「能力分三层
（Charter / Structured / Ad-hoc）」。

**用户的修正**：等一下——这两条都是 **commando 通用机制**，不是 growth
partner 特有的。任何角色（财务分析师、客服、投研）都需要知道"ad-hoc 对话
靠 Charter 注入吃饭"——这是 commando 怎么工作的事实。

**正确的归属**：

| 原计划放 playbook 的内容 | 实际归属 |
|---|---|
| 三层心智模型（Charter / Structured / Ad-hoc） | **SKILL.md**（commando 机制） |
| "Charter 上下文密度"作为一个 Calibration 决议 | **SKILL.md**（通用决议） |
| Light/Standard/Rich 三档密度的定义 | **SKILL.md**（通用档位） |
| **增长合伙人**这个角色 Charter 应该写厚哪些字段（产品一句话 / ICP / 竞品 / 渠道分层 / 漏斗 / 路线图） | **playbook**（role-specific 落地） |
| **增长合伙人**的反例（Charter 只写身份+北极星 → 聊"砍不砍雅思场景"时空泛） | **playbook**（role-specific worked example） |

**结果**：SKILL.md 增加了通用层（所有未来 playbook 自动受益）；playbook
只剩下"对增长合伙人这个角色来说，Charter 哪些字段要写厚"这种**只有这个
角色才有意义的具体建议**。

---

## PR 自检清单

打开 playbook PR 前，对你写的每一段 / 每个表 / 每个决议，逐条问：

- [ ] 这条建议换成"财务分析师"角色还成立吗？如果成立，搬去 SKILL.md。
- [ ] 这条是在解释 commando 的什么机制？如果是，搬去 SKILL.md。
- [ ] 这条出现了"commando 的 …" / "Onboarding skill 会 …" / "Runtime …"
      等字眼吗？这种内容多半属于 SKILL.md。
- [ ] 这条有具体数字 / 具体平台 / 具体产品类目吗？这是 playbook 的好
      内容标志（领域先验贵在具体）。
- [ ] 这条用了"对这个角色而言" / "这个领域里" / "经验是" 的语气吗？这是
      playbook 内容的语气标志。

---

## 灰色地带的判断法

有些内容真的不好分。一个实用判断法：

> **想象你正在写第二份 playbook（财务分析师 / 客服 / 投研）。你会原样
> 复制粘贴这段话过去吗？**
>
> - 会复制粘贴 → 它属于 SKILL.md（通用层）
> - 会修改后使用 → 它属于 SKILL.md 提出通用形式 + playbook 给 role-specific
>   修改（拆成两份内容）
> - 完全不会用 → 它属于当前 playbook（领域专属）

---

## When in doubt

倾向于**先放 SKILL.md，再被 reviewer 推回 playbook**——比反方向好处理。
playbook 里多抄了通用内容很难被发现（每份 playbook 都长得不一样）；
SKILL.md 里多了 role-specific 内容反而显眼，PR review 时一眼看出来。

---

*本文档源自 commando Onboarding skill 自测的一次真实修正
（2026-06-10）。如果你发现新的边界灰色地带，欢迎 PR 扩充本文档。*

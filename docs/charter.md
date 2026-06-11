# Charter — 数字员工的宪法

> Charter 是 commando Configuration 的第一块，也是**唯一在每次调用都自动
> 注入 context 顶部**的内容。它决定数字员工"知道自己是谁、为谁服务、不
> 能做什么"。

## 一句话理解

Charter ≠ 角色描述。Charter = **agent 每次醒来都先读一遍的那张纸**。
你写 Charter 就是在写"如果这个员工今天上班后第一件事是读一封交接信，
这封信里非有不可的内容是什么"。

## 文件位置和格式

- 路径：Configuration 目录根下的 `charter.md`
- 格式：Markdown，可选 YAML frontmatter
- 长度：取决于密度档位（见下）
- 编辑权：用户（人）。Runtime 不写 Charter；Reflection 只能**建议**修改。

## 三个密度档位（与 [`SKILL.md`](../skills/onboarding/SKILL.md) 通用决议对齐）

| 档位 | 长度 | 适用 |
|---|---|---|
| **Light** | ~500 字 | 数字员工**纯做 structured work**、用户不打算 ad-hoc 聊天 |
| **Standard** | ~1500 字 | 数字员工兼做 structured + ad-hoc（**默认推荐**） |
| **Rich** | ~3000 字+ | 用户大量依赖 ad-hoc 对话，需要 Charter 提供丰富接地材料 |

**密度核心是给 ad-hoc 对话用的接地材料**。如果你只用数字员工跑定时
任务，Light 够；如果你想随时 @ 它聊产品/灵感，必须 Standard 起。

## 标准章节结构

```markdown
# Charter: <数字员工名字>

## 1. 身份
- 名字 + 一句话画像（"前小红书内容运营 + 独立开发者圈"）
- 服务谁（用户名 / 团队 / 产品）
- 性格调性（用 3 个形容词）

## 2. 服务的产品 / 服务对象
- 产品/对象的一句话定义（纯名词+动词，不要形容词）
- 当前阶段（pre-MVP / 找 PMF / PMF 后早期 / 规模化）
- [Standard+] 产品差异化论据（vs 主要竞品）
- [Rich] 产品路线图要点

## 3. 真实 ICP / 服务对象画像
- 真正会买单/真正能触达的人是谁
- [重要] 当初想象的 ICP vs 实际付费的 ICP 差距（如果有）
- [Standard+] 主要触达渠道

## 4. 指标
- 北极星指标（必须和钱直接相关，不要用曝光/粉丝数）
- 次级指标 2-3 个
- **红线**（哪些数字突破必须立刻警报）

## 5. 方法论 / 工作框架
- 这个角色干活的核心公式（content role 有"内容公式"；
  analyst role 有"研究框架"等）
- [Standard+] 各公式的具体配比

## 6. 工作环境 / 渠道 / 触点
- 信息从哪进来
- 产物从哪出去（含发布门槛）
- 协作平台（影响 Workbench backend）

## 7. 红线 / 禁区 / 合规
- 不能做的事，每条一行
- 必有：所有对外发布必须人审（commando 全局红线，不可绕）
- 必有：AIGC 输出二次手改要求（如对外发布）
- 必有：敏感话题清单
- 角色特有的红线（如内容角色的营销密度上限、矩阵号约束）
```

## 什么应该写进 Charter，什么不该

| 内容 | 归属 |
|---|---|
| 身份 / 产品认知 / ICP / 红线 | **Charter** |
| 每天 9:15 跑 morning_sense | `schedule.yaml`，不是 Charter |
| "今天哪些任务在跑" | Workbench 实时状态，不是 Charter |
| 上周复盘要点 | Episodic Memory，由 Reflection 自动累积 |
| 实时数据（粉丝数 / 注册数）| Connectors 拉，不要硬编码进 Charter |
| 历史决策的"为什么这么定" | `.onboarding/onboarding-record.md`，溯源用 |

**反例**：把"这个月的 KPI 是注册 200 / 付费 15"硬写进 Charter——下月你改
KPI 要回来手动改 Charter。这种波动信息应在 `schedule.yaml` 或 KPI 看板里。

## 演化

- **初版**：Onboarding skill 在 Confirmation 阶段生成
- **常规迭代**：用户直接编辑 `charter.md` → commit
- **大调整**：Re-onboarding 触发 → 老 Charter 归档到
  `.onboarding/charter-v<N>.md` → 新 Charter 覆盖原位

## Role-specific 写法在哪看

各 playbook 给"这个角色的 Charter 哪些字段要写厚"的具体建议。比如
[`playbooks/growth-partner.md`](../playbooks/growth-partner.md) 决议 1.5
给出了独立产品增长合伙人 Charter 的字段清单。

---

*Charter 改坏了不会立刻报错——它只会让数字员工说话变笨。所以 Charter
是 commando 里"沉默 bug 密度最高"的文件，值得每次 PR 都让人 review。*

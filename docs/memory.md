# Memory — 数字员工的多层记忆

> Memory 是 commando Runtime 五件套之一（与 Triggers / Planner / Workbench /
> Reflection 并列）。它让数字员工能"记住做过什么、注意到什么模式、累积长程
> 经验"——这是长程营销/分析/运营 agent 区别于一次性 prompt 的根本。

## 一句话理解

Charter 解决"这个员工是谁"——人写的、稳定的、每次行动都注入。
Memory 解决"这个员工经历了什么"——agent 自动写的、累积的、按需检索。

两者**不冗余**，是互补的两个机制。

## 为什么 Charter 不能替代 Memory

| 性质 | Charter | Memory |
|---|---|---|
| **谁写** | 人（Onboarding / Re-onboarding 时） | Runtime（每次任务）+ Reflection（周期复盘）|
| **更新频率** | 低（重大决策才动） | 高（每次任务都写）|
| **载入方式** | 每次调用全部注入 context 顶部 | 按需检索注入 |
| **大小约束** | 必须有上限（~3000 字以内）| 可无限累积 |
| **content 性质** | 决策性的（"我们决定 X"）| 事实性的（"X 时间发生了 Y"）|

**关键论断**：如果让 Charter 承担所有记忆职能，会发生两件坏事：
1. Charter 无限膨胀 → 每次调用 token 成本爆炸
2. Charter 失去"宪法"的稳定性 → 每次 Runtime 自动写就改了人手定的字段

所以必须分开。

## 三层 Memory 架构（来自 atu，commando 沿用）

| 层 | 生命周期 | 内容 | 物理存储 | 注入时机 |
|---|---|---|---|---|
| **Working** | 当日（每日 reset） | 当前 daily run 的中间状态、变量、临时结论 | 进程内（内存）+ `working_memory/*.json` 落盘 | 当日同一 Skill chain 内自动可见 |
| **Episodic** | 长期累积（按日期归档） | 每次任务的**事实记录**：何时、调用了哪个 Skill、输入输出、结果、用时 | `episodic/<date>.jsonl` + 周期归档到 Workbench backend | 按需检索（语义/关键词/时间窗）|
| **Semantic** | 长期累积（人审过的精华） | **从 Episodic 中蒸馏出的模式/洞见/教训** | `semantic/*.md` + 单向同步到 backend 展示层 | 相关任务自动注入 + ad-hoc 对话按需检索 |

## 各层格式细节

### Working Memory

```
my-agent/working_memory/
├── today.json                ← 当日全量状态（每日 00:00 reset）
└── <skill>.cache.json        ← Skill 局部缓存
```

**特征**：
- 不进 git（gitignore）
- Runtime 进程退出可丢失，重启从空开始
- 适合放：当日已扫描过的 URL 集合、已生成但未审稿的草稿引用、链式
  trigger 中间产物的临时路径

### Episodic Memory

```
my-agent/episodic/
├── 2026-06-10.jsonl
├── 2026-06-11.jsonl
└── archive/                  ← 每周归档（避免 jsonl 文件过大）
    └── 2026-W23.tar.gz
```

每行 JSONL 一条事件，最简结构：

```json
{
  "ts": "2026-06-10T08:22:13+08:00",
  "task_id": "morning_sense",
  "skill": "reddit-source-mining",
  "inputs": {"subreddits": ["..."], ...},
  "outputs": {"candidates_scored": 23, "selected": 7},
  "status": "Done",
  "duration_ms": 142000,
  "notes": "..."
}
```

**特征**：
- 进 git（贡献者通过 PR 看 commit 历史就能看到 agent 的实际行为）
- 每周自动归档（防止单 jsonl 过大）
- Workbench backend 提供"只读视图"——飞书 bitable 把 jsonl 同步成
  历史表（便于人看），但**源仍在本地**

### Semantic Memory

```
my-agent/semantic/
├── content-formula-performance.md     ← 各内容公式的实际表现模式
├── channel-conversion-curves.md       ← 各渠道转化漏斗曲线
├── icp-refinements.md                 ← ICP 画像的迭代版本
├── what-doesnt-work.md                ← 失败模式备忘
└── ...
```

每份 markdown 一个**主题**，由 Reflection 写入（用户可手改）。结构建议：

```markdown
# <主题>

> 状态：active | superseded | deprecated
> 上次更新：2026-06-10
> 数据窗口：2026-01 ~ 2026-06

## 观察到的模式
<一两段事实描述>

## 证据来源
- Episodic Memory 引用：<task_id>@<date>
- 用户原话：<引自飞书 IM 对话>
- 外部数据：<来源 URL>

## 已应用的调整
- 修改了 Schedule task X 的 cron
- 调整了 Skill Y 的打分维度

## 反例 / 边界
<这条规律什么时候不成立>
```

**特征**：
- 进 git
- Reflection 周期产物，但**用户必须 review 才能 promote** 为 active
- 单向同步到 backend 展示层（飞书 Wiki / Notion）作为"agent 的工作笔记"

## Charter vs Semantic Memory 的边界规则

这是最容易混的地方。一句话规则：

> **如果一条信息应该在每次调用都注入 → Charter**
> **如果一条信息应该在相关时才注入 → Semantic Memory**

例子（增长合伙人场景）：

| 内容 | 归属 | 理由 |
|---|---|---|
| "我们的真实 ICP 是 女性+留学生+备考生" | **Charter** | 每个 skill 都该知道，影响所有判断 |
| "周二发的 Bilingual Bridge 比周四多 30% 互动" | **Semantic** | 只在做 publishing 决策时才用 |
| "外链零容忍" | **Charter** | 红线，必须每次注入 |
| "知乎长文标题加问号比加冒号 CTR 高 12%" | **Semantic** | 只在写知乎 skill 时检索 |
| "Q4 我们决定从单号扩到双号" | **Charter** | 战略决策，要稳定持有 |
| "上周一发的'雅思真题'笔记跑出 2k 收藏" | **Episodic** | 单一事件，不是模式 |

**晋升路径**：Semantic 里的某条规律持续被验证 + 用户判断"应该作为长期
约束" → 在 Re-onboarding 时**提名进 Charter**。Charter 不会自动从 Memory
升级，必须用户拍板。

## 谁写谁读：完整生命周期

| 动作 | Working | Episodic | Semantic |
|---|---|---|---|
| **每次 Skill 启动** | Runtime 准备空白 working | Runtime 准备追加新行 | Reflection 检索相关条 → 注入 context |
| **Skill 执行中** | Skill 自由读写 working | Runtime 追加输入/中间状态 | Skill 可检索读取 |
| **Skill 完成** | Working 可被同任务链下游读 | Runtime 写完整 outcome 行 | — |
| **每日终结** | Working reset | 当日 jsonl close | — |
| **每周 Reflection** | — | 扫描本周 Episodic | 蒸馏新条目（draft 状态）|
| **用户 review** | — | — | 把 draft promote 为 active |
| **Re-onboarding** | — | 作为决策证据 | 已被验证的 Semantic 可提名升 Charter |

## 长程考量（真正的 marketing agent 跑半年以上）

### 1. 防止 context 爆炸

- Charter 全量注入：必须有上限（~3000 字）。Re-onboarding 时人审压缩。
- Episodic 不全量注入：只按时间窗 + 语义检索注入相关条
- Semantic 按主题：每次调用只注入**与当前任务相关的主题文档**

### 2. 防止 Memory 噪声化

- Episodic 每周归档：active 目录只留近 8 周
- Semantic 状态机：`active` / `superseded` / `deprecated`——`active` 的
  数量必须 < 20 个主题。超了就让用户合并/退役。
- Reflection 写 Semantic 必须带"证据来源"段——没证据来源的 Semantic
  条目自动标 `draft`，用户不 promote 不上线

### 3. 防止"agent 自己写错记忆"

- Semantic 永远必须用户 review 才 active（commando 红线，不许跳）
- Episodic 是事实日志，Runtime 写入即不可改（append-only）
- Charter 永远只能人手改 + Re-onboarding 改

### 4. 数据隐私 / 法律

- Working / Episodic 含原始数据（可能涉及用户 PII / 第三方版权）
  → Configuration 仓库默认 gitignore `working_memory/` + `episodic/raw/`
- Semantic 是蒸馏后的模式，安全进 git
- 涉及用户隐私的备份策略由 Configuration 拥有者决定，commando 不替代决策

## Role-specific 建议在哪看

各 playbook 给"这个角色该累积哪些 Semantic 主题"的具体建议。比如
[`playbooks/growth-partner.md`](../playbooks/growth-partner.md) 在
Reflection 章节列出了增长合伙人典型的 Semantic 主题（内容公式表现 /
渠道转化曲线 / ICP 迭代 / 失败模式备忘）。

> 当前 playbook 中关于 Semantic 主题的建议尚未补全——这是 Memory 这份
> spec 落地后下一步要回填的 playbook 更新。

## Memory 与三层心智模型的关系

回到 [`SKILL.md`](../skills/onboarding/SKILL.md) 的三层心智模型：

| 心智层 | 谁支撑 |
|---|---|
| Charter context（常驻） | Charter + 相关 Semantic Memory 自动注入 |
| Structured work | Skill 读 Working + Episodic + Semantic，按需 |
| Ad-hoc dialogue | Charter + Semantic 按需检索 + 用户问题中提到的 Episodic |

**这意味着 Memory 同时支撑结构化任务和 ad-hoc 对话**——你跟 agent 聊
产品方向时，它不只用 Charter 接地，还会按需从 Semantic 拉相关模式
（"上次我们试过类似想法，结果是 X"）。这是长程对话有信息密度的根本
原因。

---

*Memory 是 commando 最容易被新人忽略的组件——因为它默认隐形。但 6 个月
跑下来，Memory 写得好的 Configuration 和写得糟的 Configuration，agent 的
有用度差距是数量级。*

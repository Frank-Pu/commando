# Example: 真实 Onboarding 对话记录 — LeMingle 增长合伙人

> **这是 commando 第一次 Onboarding skill 的真实 dry-run 全程对话记录**。
> 时间：2026-06-11
> 模式：Express
> Playbook：growth-partner
> 用户：Qihang（commando 项目作者，dogfood）
>
> **为什么这份 transcript 值得读**：它是文档之外**最有说服力的"Onboarding
> 究竟是怎么工作的"演示**。它也暴露了 commando 设计的真实 gap，并直接
> 反哺了 playbook 和 SKILL.md（见末尾"回流 todo 实际应用情况"）。

---

## 这次 Onboarding 揭示了 4 件事

读完整段之前，先看这 4 个结论：

1. **"recommend-then-alternatives"格式真的能让 Onboarding 变成 thinking partner**——不是问卷。
2. **Onboarding 主动追问"每位付费用户的获取路径"是关键中的关键**——这条最初不在 playbook，被本次测试发现后回填。
3. **Onboarding 承认自己判断错可以是设计的一部分**——本次 dry-run 中 Onboarding 主动收回了"小红书对 ICP 无用"的误判，反而让用户信任度提升。
4. **Pre-PMF 配比 ≠ PMF 后配比**——这本是默会知识，但 playbook 之前没写。

---

# 完整对话

## Phase 0 · Role Scoping

### Skill 启动

> 👋 你正在运行 **commando /onboarding**。
>
> 我来帮你把"我想造一个数字员工"变成磁盘上一份能跑的 Configuration 目录（`./my-agent/`）。聊完你会拿到 charter.md / schedule.yaml / skills/ / connectors.yaml 等文件。
>
> 开始前两件事先对齐：
>
> **1. 时间预算**：完整模式（60-120 分钟）/ Express 模式（20-30 分钟，明确接受 v0.1 粗糙）
>
> **2. Configuration 落到哪里**：默认 `./my-agent/`

### User: Express 模式

### Skill: 进 Phase 0

> Express + `./my-agent/`，确认。
>
> 📁 当前可用 playbook：`growth-partner` / `_generic`（兜底）。
>
> **Phase 0 · Role Scoping（3 问）**：
>
> 1. 这个数字员工**为谁服务**？
> 2. **主要职能**一句话
> 3. **日常节奏**

### User: 完整回答

> 这个数字员工会作为我独立开发产品 LeMingle 的增长合伙人。
>
> 他的主要职能是负责增长、内容、数据分析等一系列的全链路工作：
> 1. 从创意生成到素材生成
> 2. 发布后的数据跟踪
> 3. 与我探讨日常的增长想法
>
> 关于日常节奏，我希望有一个比较固定的产出流程和时间点，并且加入一些周期性的盘点。整体的配合方式和节奏，就像是跟一个真正的人类合伙人在共同为一个产品的增长而努力。

### Skill: 匹配 playbook + 处理 "ad-hoc 对话" 边界

> 匹配清楚：**growth-partner playbook**。
>
> 核心假设：数字员工是配了好程式的实习生，不是有判断力的合伙人。
>
> **关于"与我探讨日常增长想法"——我特意停一下**：这次不当成新增 Skill，
> 因为它在三层心智模型的**第三层（Ad-hoc dialogue）**，默认全开：
>
> - 你随时 @ 它，它带着 Charter 上下文跟你聊
> - 不需要 strategy-discussion Skill
> - 但这意味着 **Charter 必须写得够厚**——Calibration 会拍板。
>
> Express 模式我会**两批问完 6 个维度**。

> 📝 **设计 commentary**：这是上一轮测试发现 bug 后修正的关键时刻。在此之前
> 的 SKILL.md 版本会把"探讨增长想法"翻译成新增 Skill，从而错误膨胀
> Configuration。修正后，三层心智模型让 Onboarding 直接给出正确反应。

---

## Phase 1 · Discovery Round 1（产品 / ICP / 指标）

### Skill: 3 个 Discovery 维度问题

> **Q1 · 产品**：一句话定义 + 当前阶段 + 月活/付费量级
>
> **Q2 · 真实 ICP**：付费用户画像 + 与最初设想的差距
>
> **Q3 · 北极星 + 红线**：和钱挂钩的指标 + CAC 红线 + 90 天目标

### User: 完整答案

> LeMingle 简单来说是一个帮助外语学习者自然记住地道表达、提升词汇量的浏览器插件。
>
> 1. **项目现状**
>    目前产品还处于探索 PMF 的过程中。之前的尝试主要集中在小红书、知乎等平台的内容营销和 SEO。
>    - 注册用户：数十
>    - 付费用户：个位数 人
>    - 月活数据：目前较难统计
>
> 2. **用户画像 (ICP)**
>    目前的付费用户呈现出明显的共性：他们都是海外高净值、高素质的精英群体（如律师、医生、科研人员）。
>    - 案例一：一名 用户 A，专门负责在美国服务跨语言专业场景
>    - 案例二：一名 用户 B · 海外华人研究员
>    这与我最初设想的 ICP 基本一致。
>
> 3. **核心指标与目标**
>    - 北极星指标：商业化收入和付费用户数
>    - 获客成本 (CAC)：倾向于自然增长和内容营销
>    - 90 天目标：20 个付费用户

### Skill: 反应 + 主动追问（**关键时刻**）

> **我必须停一下**：你的描述里有两处张力。
>
> **张力 1**：ICP 是海外律师/PhD，主渠道是小红书/知乎——这两个根本不在
> 同一个世界。用户 A + 用户 B 是 LinkedIn / 学术 Twitter
> 用户，**不是**小红书用户。
>
> **张力 2**：你在 pre-PMF 状态（n=几个 付费），但已经在搭内容供应链工程。
> Playbook 警示——pre-PMF 阶段的增长合伙人，主战场应该是「找出谁是真用户」。
>
> **关键缺失数据点**：你那 几个付费用户是怎么来的？
> - 是从小红书/知乎过来的吗？
> - 还是 LinkedIn / 朋友推荐 / 别的？
> - 你和他们有过直接交流吗？

> 📝 **设计 commentary**：**这条追问最初不在 playbook 里**。是 Onboarding
> 临场判断"信息不够，不能直接进下一维度"。后续证明这一追问救了整个
> Configuration——已回填到 playbook 作为强制 Discovery 追问点。

### User: 回答（**真信号**）

> 这两个付费用户中，用户 A那位是从小红书发的一个图文帖子吸引过来的。
> 我跟他有过线上比较深入的沟通...他给我们提了一些产品建议：
> 1. 他觉得初次翻译的某个核心功能比较好用
> 2. 希望我们也能够补齐相应的功能
> 后面根据他的建议，我又做了非常多的迭代。
>
> 至于用户 B，我真不知道他是从哪里来的。
> 就在 支付后台付费记录里面，莫名其妙就多了一个人，给我们开了三个月的会员。

### Skill: 收回前判 + 重新框架（**关键时刻 2**）

> **OK，停。我刚才那条"小红书对你 ICP 无用"的判断——错了，要收回。**
> 你给的反例（用户 A 从社媒主线来 + 深聊 + 反向驱动了产品迭代）直接打掉了
> 我的论断。承认错误是 Onboarding 该有的样子，不是 bug。

> 📝 **设计 commentary**：Onboarding 主动收回判断是 SKILL.md 人格设定
> "thinking partner 而非僵化系统" 的实际体现。测试证明这一设定在压力下
> 真的生效。

> ICP 修正：从"用户 A 类"窄 → "海外华人专业人士"宽（仍在中文社交圈）。
> 渠道判断修正：小红书保留主线，但**内容切入点**必须从"留学生/备考生"
> 转向"海外华人专业人士的工作语言痛点"。
>
> **但这次对话最重要的信号根本不是渠道**——是**用户 A 案例本身**：
>
> 小红书一篇笔记 → 用户 A 付费 → **深度交流** → 提"某个核心功能"建议 → **大量迭代**
>
> 这是**典型 pre-PMF 增长循环**——内容是钓饵，**真正的价值在和单个用户的深聊**。
> 增长合伙人在这种状态下，工作重心是：
> 1. **少而精**的内容（一周 1-2 篇）
> 2. **捕捉每一个进入的用户**
> 3. **系统化记录用户原话**
> 4. **帮你准备和复盘 1-on-1 用户访谈**
>
> **还有一个"真问题"必须立刻处理**：用户 B莫名其妙在支付后台冒出来
> ——你不知道用户从哪来。这是**漏斗黑箱**——增长合伙人必须把它列为前置阻塞。

---

## Phase 1 · Discovery Round 2（资源 / 渠道 / 红线）

### Skill: 3 个剩余维度

> Q4 · 可用资源：审稿时间 / 模型 / 工具栈
> Q5 · 渠道布局：主线 / 储备 / 暂缓
> Q6 · 红线与禁区：发布人审 / AIGC / 营销密度 / 矩阵号 / 其他

### User: 完整答案

> 因为我日常还有一个在互联网大厂的 AI 产品经理工作，工作时间比较长，
> 所以我每天能挤出来给数据员工审稿的时间大概在 **15 到 30 分钟**。
>
> 关于模型和工具的使用：
> 1. 我愿意用最强的 Claude 模型...用 Claude Code 来驱动内容生产
> 2. 日常协作平台用的是**飞书和飞书 CLI**
>
> 渠道布局：
> - 主线小红书保留
> - LinkedIn 和 X 中文圈可以尝试
> - 知乎 SEO 建议保留
>
> 策略调整：最关键的一点是，你刚刚纠正了我关于发帖节奏的想法。不应该
> 大量反复生产某一种形式的内容，而是先切入 ICP，少量发布他们感兴趣的内容。
>
> AIGC 比例：之前说 AIGC 必须修改 20% 才能发，这个标准可以放宽一点，
> 修改 5% 到 10% 也可以。
>
> 风控：账号情况是产品主号+个人账号。**国内社媒和海外社媒对内容风控要求
> 是不一样的**。

### Skill: 两条 Pushback（**Opinionated Calibration 实战**）

> **打回 1**：AIGC "5-10% 修改"这个框架本身是错的。
>
> **正确的红线不是百分比，是改动质量**：
> - 必做：清掉 AI 套话 transition + 加 Qihang 个人声音 + 删空泛形容词
> - 只要这三件做到，整体改动 5-10% 都没问题
>
> **打回 2**：你 15-30 min/天，**但想试 4 个渠道**。数学上不工作：
> - 小红书 2 篇/周 = 20 min/周
> - 知乎月长文 = 60 min/月
> - LinkedIn 需冷启动 2 周
> - X 中文圈同样冷启动
>
> Pre-PMF + 15-30 min/天 这个约束下，最多支撑 **2 个真在跑的渠道**。
> 强推荐：保留小红书 + 知乎，暂缓 LinkedIn/X。

### User: 接受 1 和 2

> 📝 **设计 commentary**：两条 pushback 都没用"你考虑一下"或"以下是几种
> 选择"的中立摊牌式发问——而是先给推荐再列替代。这是 SKILL.md 守则
> "绝对禁止中立列举"的实际效果。

---

## Phase 2 · Calibration

### Skill: 7 条决议一次性 batch

> 进 Calibration。**7 条决议**一次性给推荐 + 理由，你扫一遍哪条要改。
>
> 决议 1 · Structured Work 边界：内容供应链 + 用户研究支持
> 决议 2 · Charter 密度：Rich（3000+ 字）
> 决议 3 · 内容公式（偏离 playbook）：A 50% / B 用户案例放大 30% / C 20%
> 决议 4 · 渠道分层：小红书主线 + 知乎储备 + 暂缓 LinkedIn/X
> 决议 5 · 任务节奏：8 个 task，总审稿 ~25 min/周 + 30 min/月
> 决议 6 · Skill 启用清单：3 imported + 4 draft
> 决议 7 · Backend + 红线明文化：飞书 + 7 条红线
>
> 🚨 **Configuration 之外的前置事项**：归因黑箱要先解（Plausible/Umami + UTM）

> 📝 **设计 commentary**：决议 3 把 playbook 默认的"爆款复刻 30%"换成
> "用户案例放大 30%"——这是 Onboarding **临场判断**用户的 pre-PMF 状态
> 而做的偏离。后已回填到 playbook 作为 PMF 状态分档配比的 Pre-PMF 选项。

### User: 都支持

---

## Phase 3 · Confirmation

Skill 进入 batch 写文件模式，产出 13 个文件：

```
my-agent/
├── README.md                          ← 含归因前置阻塞 + atu 关系决策
├── charter.md (175 行)                ← Rich 密度，7 节标准结构
├── schedule.yaml (164 行)             ← 8 task pre-PMF 轻节奏
├── connectors.yaml (66 行)            ← 飞书 + 5 source 占位
├── skills/
│   ├── reddit-source-mining/SKILL.md   (imported)
│   ├── xhs-bilingual-bridge/SKILL.md   (imported)
│   ├── marketing-kit/SKILL.md          (imported)
│   ├── outlet-rss-scan/SKILL.md        (draft)
│   ├── user-feedback-curator/SKILL.md  (draft) ← pre-PMF 关键 ROI
│   ├── user-call-prep/SKILL.md         (draft)
│   └── user-call-debrief/SKILL.md      (draft)
├── .onboarding/
│   ├── discovery-notes.md
│   ├── calibration-decisions.md
│   └── onboarding-record.md
└── backends/ workbench/ memory/{working,episodic,semantic}/   ← Runtime 累积
```

### Skill: 结束语

> 这就是你的数字员工 v0.1。
>
> 它**一定有地方不对**——可能是 ICP 收窄不够、可能是内容公式比例错、
> 可能是 schedule 节奏不对。这是正常的，不是你或我的问题，是这种活儿的本质。
>
> 接下来 2 周按它跑，**真有数据**之后回来用 `commando reonboard --refine`
> 再聊一轮。
>
> Re-onboarding 不会清空这次的产物——它在原 Configuration 上做 diff 增量调整。

---

# 测试同时验证了一批设计

| 设计 | 测试验证情况 |
|---|---|
| 三层心智模型（Charter/Structured/Ad-hoc） | ✅ "探讨增长想法"没被错塞进 Skill |
| Opinionated Calibration（先推荐再列替代） | ✅ AIGC % / 4 渠道 两次主动 pushback 都生效 |
| Discovery 中主动质疑用户自评 | ✅ "ICP 与我想的一致"被追问后翻盘 |
| Onboarding skill 承认自己错 | ✅ "小红书对你 ICP 无用"主动收回 |
| `.onboarding/` 目录三件套 | ✅ discovery + calibration + record 全产出 |
| Charter Rich 密度 + 红线明文化 | ✅ 文件实际产出且可读 |

---

# 回流 todo 实际应用情况

本次测试发现的设计 gap，已**当场**应用到 commando 主仓：

| 回流 todo | 应用位置 | 状态 |
|---|---|---|
| "几个 paid user 怎么来的" 作为强制 Discovery 追问点 | [`playbooks/growth-partner.md`](../playbooks/growth-partner.md) Discovery 维度 2 新增"强制追问"段 | ✅ 已应用 |
| Pre-PMF / PMF 后 / 规模化 三套内容公式配比 | [`playbooks/growth-partner.md`](../playbooks/growth-partner.md) 决议 2 改为分档配比 | ✅ 已应用 |
| Configuration 之外的前置阻塞 (归因黑箱) | [`playbooks/growth-partner.md`](../playbooks/growth-partner.md) 新增决议 4 之前的"强制前置检查" + [`skills/onboarding/SKILL.md`](../skills/onboarding/SKILL.md) Phase 3 新增"前置阻塞"段 | ✅ 已应用 |
| 本次完整对话存为 example transcript | 当前文件 ([`docs/example-onboarding-transcript.md`](example-onboarding-transcript.md)) | ✅ 已应用 |

---

# 给读者的话

如果你看完想跑自己的 Onboarding：

1. 用 Claude Code 在 commando 仓库根目录打开
2. 把 [`skills/onboarding/SKILL.md`](../skills/onboarding/SKILL.md) 加载到对话（"现在请扮演 commando onboarding skill"）
3. 告诉它："开始 Onboarding，输出目录 `./my-agent/`，Express 模式"
4. 跟它聊 20-40 分钟
5. 看产出，按本 transcript 对照"它哪里学会了 / 哪里还差"

发现新 gap 欢迎 PR——commando 仍在 0.x，社区反馈是这阶段最稀缺的资源。

---

*本 transcript 是 commando 第一次 Onboarding dry-run 的实录，
内容经过轻度编辑（删了文件 batch 写入的具体内容、保留对话流和决策追溯）
以保持可读性。完整决策溯源见 [`my-agent/.onboarding/`](../my-agent/.onboarding/).*

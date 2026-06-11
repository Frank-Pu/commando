# LeMingle 增长合伙人 · 阿土

> **由 commando `/onboarding` 生成**
> **版本**：v0.1
> **生成**：2026-06-11 (Express mode)
> **playbook**：growth-partner

这是一份**可跑、待调**的 Configuration。Onboarding 给你的不是终态——是
一个**v0.1 起点**，跑 2 周看真实数据后回来 `commando reonboard --refine`。

## 这里是什么

| 文件 | 内容 |
|---|---|
| [charter.md](charter.md) | 阿土的宪法 v0.1（Rich 密度，~250 行）—— 身份/产品/ICP/指标/方法论/渠道/红线 |
| [schedule.yaml](schedule.yaml) | 8 个 task：每日信息源扫描 + 周二/五小红书初稿 + 月度知乎长文 + 周度复盘 + 周日反思 + 用户访谈支持 |
| [connectors.yaml](connectors.yaml) | Backend：飞书；Sources：Reddit / RSS / xhs / zhihu / stripe / plausible |
| [skills/](skills/) | 7 个 Skill：3 个 imported（待 commando install）+ 4 个 draft（待你工程实现）|
| [.onboarding/](.onboarding/) | 完整对话记录 + 决议溯源（未来 Re-onboarding 用） |

## 🚨 跑起来之前必须做的事

### 1. 部署归因工具（**最高优先级**）

用户 B 凭空在支付后台 出现说明你**当前完全没有渠道归因**。在装好之前，
`weekly_data_review` 任务的归因部分会跑空，所有渠道策略都是瞎猜。

具体动作：
- 部署 [Plausible](https://plausible.io/) 或 [Umami](https://umami.is/)（免费、不打扰用户、GDPR 友好）
- 在 LeMingle 注册流加一个**"你从哪里知道我们的"** 选项
- 小红书 / 知乎所有发布链接打 UTM

### 2. 决定 commando Runtime 实现状态

当前 commando CLI 还没上线（README 见 commando 主仓 "0.x 阶段在做什么"）。
所以这个 Configuration 暂时跑不起来——是**为未来 commando Runtime 准备
的设计原型**。

如果你**急着用**：
- 把 charter.md 加载到 Claude Code 当 system 用 → 即得 ad-hoc 对话 agent
- 把 schedule.yaml 的 cron 改写成 launchd plist → 即得简单的定时驱动
- 把 skills/ 的 draft 一个个工程化 → 即成真 atu 的下一代

如果你**不急**：
- 等 commando 仓库工程化 → 这份 Configuration 直接被 `commando run` 加载

### 3. 决定 atu 和这份 Configuration 的关系

atu 已经在跑了。这份 Configuration 是**修正版本**（Pre-PMF 特调 + 新增
用户研究 skills）。三种处理方式：

| 选择 | 含义 |
|---|---|
| **A. 替代** | 把这份 Configuration 替代 atu 现有的 charter + schedule + skills |
| **B. 并行** | 这份作为 commando 设计原型，atu 继续按原版跑 |
| **C. 合并** | 把这份的 4 个新 draft skill 抽出来加进 atu，其他不动 |

我（阿土）推荐 **C**——你现在 atu 跑得好的不要动，只把"用户研究支持"
那 4 个 draft skill 工程化加进去，立刻提升 pre-PMF 的关键 ROI。

## 下一步（如果走 commando 原型路线）

```bash
# 1. 进入 Configuration 目录
cd my-agent

# 2. (未来) 接 backend
commando connect feishu              # 让本地 agent 生成 driver

# 3. (未来) 物化 scheduler 到飞书
commando materialize

# 4. (未来) 跑起来
commando run --task morning_sense
```

当前没 commando CLI，上面是占位说明。

## v0.1 一定有什么错

这是 Express 模式快速跑出来的 v0.1。预测会错的地方：

- **ICP 描述还太宽**（"海外华人专业人士"）—— 跑 2 周后用真实 paid user
  数据可以收窄
- **内容公式 50/30/20 是猜的**—— 跑 2 周后用单笔记 attribution 数据可以微调
- **小红书每周 2 篇可能还是多**—— 如果你审稿压力大，砍到 1/周也对
- **draft skill 还没工程实现**—— 没工程化的 skill 等于不存在

所以：**跑 2 周，回来 `commando reonboard --refine`**。带着真实数据来，
那时候的校准比第一次准 10 倍。

## 这次 Onboarding 暴露的设计反馈（给 commando 项目）

见 `.onboarding/onboarding-record.md` 末尾的"回流 todo"——本次测试发现的
4 条 commando playbook / SKILL.md 应该更新的点。

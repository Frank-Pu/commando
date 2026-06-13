# commando

> ⚠️ **0.x · docs-first 阶段** — 设计骨架完整，flagship Onboarding skill 可手动运行；`commando` CLI 实现等社区反馈定优先级。详见 README 末尾"当前阶段坦诚说"。

> 把 AI 角色配置变成一个工程问题，而不是 prompt 玄学。
>
> **Runtime 是商品，Configuration 是护城河。**

commando 是一个开源的**数字员工 Configuration 框架**。它不在 Runtime 那一层
和 Claude Agent SDK / Pydantic AI / LangGraph 竞争——commando 故意把
Runtime 做得最小，把全部精力放在让 **Configuration 可被生成、版本化、
分发、复用、评测**上。

## 60 秒上手理解

| 你想 | commando 给你 |
|---|---|
| 为自己的产品/团队造一个"数字员工" | 跑 `commando onboard`——2 小时对话之后磁盘上多一个 v0.1 可跑的 Configuration 目录 |
| 不绑死任何模型 / 平台 | 用你已经付费的 Claude Code / Codex / Kimi 跑 Onboarding；用你已经在用的飞书 / Notion / 钉钉做 Workbench |
| 不自建 dashboard / UI | scheduler 看板物化到你已在用的协作平台原生视图（飞书 bitable / Notion database / ClickUp...） |
| 接入新平台不等官方支持 | `commando connect <platform>`——让你本地的 agent 当场生成 backend driver，commit 到你自己仓库 |
| 看一个真实活着的例子 | [examples/lemingle-growth-partner/](examples/lemingle-growth-partner/)——服务 [LeMingle](https://lemingle.com) 跑了 6+ 个月 |

## 0.x 阶段在做什么

commando 当前是 **docs-first 阶段**——设计骨架已成形，工程实现还在等社区
反馈定优先级。当前仓库的核心交付物：

### Spec 文档

- [docs/charter.md](docs/charter.md) — 数字员工的宪法
- [docs/scheduler.md](docs/scheduler.md) — 数字员工的产品表面（一张表两种 row）
- [docs/skill.md](docs/skill.md) — Skill 的格式 + commando 扩展（基于 Claude Code Skills）
- [docs/memory.md](docs/memory.md) — 三层记忆：Working / Episodic / Semantic
- [docs/capabilities.md](docs/capabilities.md) — 能力词典（跨 backend 通用语义）
- [docs/connectors.md](docs/connectors.md) — Backend + Source 连接层
- [docs/backend-driver.md](docs/backend-driver.md) — Driver 怎么由你本地 agent 生成
- [docs/playbook-vs-skill-boundary.md](docs/playbook-vs-skill-boundary.md) — 贡献 playbook 前必读
- [docs/example-onboarding-transcript.md](docs/example-onboarding-transcript.md) — **真实 Onboarding 全程对话记录**（最好的 demo 素材）

### 旗舰 Skill

- [skills/onboarding/SKILL.md](skills/onboarding/SKILL.md) — Onboarding skill：
  3 阶段对话产出 v0.1 Configuration

### Playbooks

- [playbooks/growth-partner.md](playbooks/growth-partner.md) — 独立产品增长合伙人
  （来自 atu 半年实跑沉淀）
- [playbooks/_generic.md](playbooks/_generic.md) — 兜底
- 其他职能（财务 / 客服 / 投研 / 教育 …）—— 欢迎 PR

### 示例 Configuration

- [examples/lemingle-growth-partner/](examples/lemingle-growth-partner/) — 阿土
  ＝ 服务 LeMingle 的真实数字员工，跑了 6+ 个月

### Skill Registry

- [skills.json](skills.json) — 社区共享 Skill 索引

## 设计原则

1. **Runtime 故意做小**。等 Runtime 落地你会发现它就是 500-1000 行 Python：
   Planner + Workbench + Memory + Skill runner + Capability registry。
2. **不绑模型**。用户用自己的 Claude Code / Codex / Kimi / GLM / Qwen CLI
   跑 Onboarding 和日常 Skill。
3. **不绑 backend**。`commando connect <platform>` 让用户本地 agent 生成
   driver 代码，留在用户仓库——commando 不维护多个官方 driver。
4. **不绑 UI**。Scheduler 看板物化到协作平台原生视图。本地 `commando dashboard`
   只做"裸 hello-world"用的迷你 HTML。
5. **复用 Claude Code Skills 格式**。commando Skill = Claude Code Skill +
   5 个 commando frontmatter 扩展。

## 数字员工能力的三层（始终持有的心智模型）

| 层 | 性质 | 由谁驱动 | 是否需要 Skill |
|---|---|---|---|
| **Charter context** | 常驻背景，每次调用自动注入 | Charter | 不需要 |
| **Structured work** | 有 cron / trigger 的循环活 | Schedule + Skill | **需要 Skill** |
| **Ad-hoc dialogue** | 用户随时 @ 它聊任何事 | IM + Charter + LLM base | 不需要 Skill |

这层心智模型搞错的最常见反模式：把所有能力都往第 2 层塞，导致 Configuration
误以为很重——其实大部分对话能力在第 3 层就免费拿到。

## 怎么用（当前手动模式）

> ⚠️ commando CLI 还没实现。下面是预期的命令形态——当前手动加载 Onboarding
> skill 也能产出 Configuration。

```bash
# 安装（未来）
pip install commando

# 跑 Onboarding（产出 ./my-agent/ Configuration 目录）
commando onboard

# 给 Configuration 接 backend
cd my-agent
commando connect feishu          # 用本地 agent 生成 feishu backend driver
commando materialize             # 把 scheduler / charter / kpi 看板渲染到飞书

# 跑起来
commando run --task hello_world
commando dashboard               # 本地 mini dashboard
```

**今天就能用**：

1. 用 Claude Code 在本仓库根目录打开
2. 把 [skills/onboarding/SKILL.md](skills/onboarding/SKILL.md) 当作 system
   指令载入
3. 告诉它"开始 Onboarding，输出目录 ./my-agent/"
4. 跟它聊 60-120 分钟（Express 模式 25-30 分钟）
5. 拿到一份可跑的 Configuration 骨架

**也可以先看看 dashboard 长什么样**：

```bash
pip install pyyaml          # 唯一依赖
python dashboard/server.py  # 浏览器自动打开 http://127.0.0.1:7878
```

teal + coral 配色 / EN-中切换 / dark mode / 审稿按钮跳本地 markdown。
详见 [dashboard/README.md](dashboard/README.md)。

## 与 atu 的关系

[atu](https://github.com/Frank-Pu/atu) 是 commando 的 dogfood——一个跑了
6+ 个月的真实"LeMingle 增长合伙人"数字员工。atu **先于** commando 存在，
commando 反过来从 atu 的设计经验中抽象出来。

atu 不会被重写进 commando——它独立演化，作为 commando 的官方参考
Configuration（[examples/lemingle-growth-partner/](examples/lemingle-growth-partner/)）。

## 贡献

最稀缺的贡献：

1. **新 playbook**——你的角色（财务 / 客服 / 法务 / 投研 / 教育 …）没有
   专属 playbook，把经验沉淀成 PR。
   **写之前请先读** [docs/playbook-vs-skill-boundary.md](docs/playbook-vs-skill-boundary.md)。
2. **Skill 提交到 Registry**——PR 改 [skills.json](skills.json) 加一条。
3. **Backend driver 范本**——把你本地 `commando connect` 生成的 driver
   清理一下 PR 回来作为社区参考实现。

不需要的贡献：自建 GUI / 新增 Runtime 抽象 / 和某个 SaaS 深度绑定。
这些是反 commando 设计原则的。

## 当前阶段坦诚说

**已有**：完整设计骨架 + 旗舰 Onboarding skill + 1 份 playbook + 真实
example Configuration + 能力词典。

**没有**：`commando` CLI 实现 / Runtime Python 代码 / 出厂 backend driver。

**为什么先发文档**：commando 的核心赌注是"Configuration 是工程问题，
不是 prompt 玄学"——这个判断本身需要先让社区讨论再决定是否值得花数月
工程。docs-first 也是 commando 设计哲学的 dogfood。

如果你看完觉得这套思路 work，**最有用的反馈不是 "什么时候出 CLI"——
是 "我想跑 Onboarding 但你的 playbook 没覆盖我的角色"** 这种具体匹配
问题。

## License

[MIT](LICENSE).

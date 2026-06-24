# commando

> Configure an AI digital employee in 25 minutes. Works with whatever AI tool you already use — Claude Code, Cursor, Windsurf, Codex, Kimi, GLM, Qwen, Doubao, MiniMax, Gemini. commando never picks an LLM for you.
>
> **Runtime is commodity. Configuration is the moat.**

commando is an open-source **Configuration framework** for digital employees. It does not compete at the Runtime layer with Claude Agent SDK / Pydantic AI / LangGraph — commando keeps Runtime deliberately tiny and invests everything in making **Configuration generatable, versionable, shareable, and inspectable**.

```
你 → commando onboard         ← 25 分钟在你已有的 CLI 里走 Discovery / Calibration
       ↓
       ./my-agent/            ← charter / skills / schedule.yaml 在磁盘上是你的
       ↓
   commando go-live           ← 连飞书 + 装 launchd
       ↓
   第二天 8:00 你的飞书收到第一张卡片
```

---

## Install (30 秒)

```bash
curl -fsSL https://raw.githubusercontent.com/Frank-Pu/commando/main/install.sh | sh
```

会克隆仓库到 `~/.commando` 并把 `~/.commando/bin` 加进 PATH。

手动安装：

```bash
git clone https://github.com/Frank-Pu/commando.git ~/.commando
export PATH="$HOME/.commando/bin:$PATH"   # 或 append 到 ~/.zshrc / ~/.bashrc
```

依赖：Python 3.9+ · git · 一个 AI 工具（详见下表）

### 你的 AI 工具怎么接进来

| 场景 | 用什么 |
|---|---|
| **Onboarding 对话** · ad-hoc 聊天 | **任意 AI 工具**：CLI（Claude Code, Codex, Kimi, GLM, Qwen, Doubao, MiniMax, Gemini）或 IDE（Cursor, Windsurf, VS Code Copilot, JetBrains AI, Claude Desktop…）都行——它只是读 `skills/onboarding/SKILL.md` 跟你聊 |
| **定时 task（launchd / systemd 触发）** | 需要 PATH 里有 CLI（OS 调度器只能调 CLI），或 `ANTHROPIC_API_KEY` 走 SDK 兜底 |
| **强制指定** | `export COMMANDO_LLM=kimi`（任一注册的 CLI 名） |

### 我只用 IDE，没装 CLI——怎么跑？

完全可以。`skills/onboarding/SKILL.md` 是纯 markdown 指令集，任何 IDE agent（Cursor / Windsurf / VS Code Copilot / JetBrains AI / Claude Desktop / ChatGPT desktop）只要有 file Read + Write 工具就能跟着跑。两条路：

**路径 A · 让 commando 告诉你要粘啥**
```bash
cd ~/.commando
commando onboard --print-prompt    # 直接打印一段可粘贴的 kickoff prompt
```
然后在你的 IDE 里粘贴它即可。`commando onboard` 不带 flag 时如果检测到没装任何 CLI，也会自动走这条路径。

**路径 B · 直接在 IDE 里发起**

在你 IDE 的 AI 聊天框里粘：

> 请打开本仓库的 `skills/onboarding/SKILL.md` 并完整读一遍。读完之后扮演里面定义的 Onboarding 主持人角色，按 4 阶段流程（Role Scoping → Discovery → Calibration → Confirmation）带我走一遍。Confirmation 阶段请真的用 Write 工具把 Configuration 文件写到 `./my-agent/`，不要只在聊天里展示内容。

完成后回到终端跑 `commando go-live`（这部分不需要 IDE，纯 CLI 就行）。

### IDE 用户的 build-skills 也不需要 API key

Onboarding 产出的 draft skills 需要 LLM 来填 prompt body。**如果你只用 IDE 没装 API key**，subprocess 调 `claude -p` 会撞 auth 失败（dogfood 实测）。这时候用：

```bash
commando build-skills --print-prompts
```

它会打印一份**完整自洽的元提示词**（含 charter + playbook + 每个 draft skill 的元信息），你直接粘进你的 IDE agent（Cascade / Cursor / Claude Code 都行），让宿主 agent 自己一次性把所有 SKILL.md 写好。没 subprocess、没 API key、不需要任何额外配置。

`commando go-live` 的 Step 4 检测到你没 `ANTHROPIC_API_KEY` 时也会自动推荐这条路径。

验证：

```bash
commando --version    # commando, version 0.1.0
commando --help
```

---

## 你的前 25 分钟

```bash
commando onboard
```

发生什么：

| Step | 时间 | 内容 |
|---|---|---|
| 1 | 即时 | commando 检测你的 agent CLI（claude / codex / kimi / glm / qwen） |
| 2 | ~25 min | 在你已有的 CLI 里走 **Phase 0 Role Scoping → Phase 1 Discovery → Phase 2 Calibration → Phase 3 Confirmation** |
| 3 | 即时 | 磁盘上多一个 `./my-agent/`：`charter.md`、`skills/`、`schedule.yaml`、`.onboarding/` |
| 4 | ~5 min | onboard 退出后自动跳 **`commando go-live`**：校验配置 → 连飞书 IM → 装 launchd → "You're live" |

第二天到点：你飞书收到第一张卡片。

---

## 一眼看清自己的数字员工

```bash
commando status
```

```
Configuration
  ✓  charter.md  (7969 bytes)
  ✓  skills: 8 total, 5 active
  ✓  schedule.yaml: 6 cron, 3 manual

LLM backend (Runtime is commodity)
  ✓  agent CLI: Claude Code (/opt/homebrew/bin/claude)

Connectors
  ✓  Feishu IM: my-agent/credentials/feishu.yaml

OS scheduler
  ✓  6 launchd job(s) installed

  Upcoming firings:
  · Tue Jun 24 08:00   morning_sense
  · Tue Jun 24 11:00   xhs_draft_tue
  · Fri Jun 27 11:00   xhs_draft_fri

Recent activity (episodic memory)
  ✓  4 event(s) today
```

---

## 子命令清单

| 命令 | 干嘛 |
|---|---|
| `commando onboard` | 在你的 CLI 里走 Onboarding 对话，产出 `./my-agent/` |
| `commando init`    | 直接拷贝一份样例 Configuration（不走对话，看效果用） |
| `commando go-live` | 收尾向导：校验 + 连 IM + 装 launchd |
| `commando status`  | 健康快照 |
| `commando run --task <id>` | 手动触发一个 task |
| `commando schedule install --apply` | 把 cron tasks 装进 launchd |
| `commando schedule list / uninstall` | 看 / 卸 launchd job |
| `commando connect im-feishu` | 飞书 IM 推送向导 |
| `commando dashboard` | 本地 web 看板 |
| `commando route --demo <level> --apply` | 发一张测试 IM 卡片 |

---

## 三层心智模型（请先理解这个再用）

| 层 | 性质 | 由谁驱动 | 需要 Skill 吗 |
|---|---|---|---|
| **Charter context** | 常驻背景，每次调用自动注入 | `charter.md` | 不需要 |
| **Structured work** | 有 cron / trigger 的循环活 | `schedule.yaml` + `skills/` | **需要 Skill** |
| **Ad-hoc dialogue** | 用户随时 @ 它聊任何事 | IM + Charter + base LLM | 不需要 Skill |

最常见的反模式：把所有能力都往第 2 层塞，导致 Configuration 误以为很重——其实大部分对话能力在第 3 层就免费拿到。

---

## 设计原则

1. **Runtime 故意做小**。Runtime = 一个 LLM 调用 + episodic 写盘。不到 200 行 Python。
2. **不绑模型 / 不绑工具表面**。Onboarding 在你已经在用的 AI 工具里发生——CLI 或 IDE 都行（Claude Code, Cursor, Windsurf, Codex, Kimi, GLM, Qwen, Doubao, MiniMax, Gemini…）。定时 task 因为是 launchd 调起，需要 CLI 在 PATH 或 API key。`$COMMANDO_LLM=kimi` 可强制指定。
3. **不绑调度器**。`schedule.yaml` 翻译成 launchd plist / systemd timer，由 **OS 驱动**触发——commando 不写自己的 daemon。
4. **不绑 backend**。`commando connect <platform>` 让你本地 agent 生成 driver 代码，留在你自己仓库。
5. **不绑 UI**。Scheduler 看板物化到你协作平台原生视图（飞书 bitable / Notion database / ClickUp）。本地 `commando dashboard` 是裸 hello-world 用的。
6. **复用 Claude Code Skills 格式**。commando Skill = Claude Code Skill + 5 个 commando frontmatter 扩展。

---

## 真实例子

[examples/lemingle-growth-partner/](examples/lemingle-growth-partner/) — 阿土：服务 [LeMingle](https://lemingle.com) 的真实数字员工，6+ 个月连续运行。`commando init` 默认拉的就是这个。

[atu](https://github.com/Frank-Pu/atu) 是 commando 的 dogfood——atu 先于 commando 存在，commando 反过来从 atu 的设计经验中抽象。atu 不会被重写进 commando，作为参考实现独立演化。

---

## Specs（设计文档）

- [docs/charter.md](docs/charter.md) — 数字员工的宪法
- [docs/scheduler.md](docs/scheduler.md) — 一张表两种 row 的产品表面
- [docs/skill.md](docs/skill.md) — Skill 格式 + commando frontmatter 扩展
- [docs/memory.md](docs/memory.md) — Working / Episodic / Semantic 三层
- [docs/event-bus.md](docs/event-bus.md) — Episodic 作为 event bus + IM routing
- [docs/capabilities.md](docs/capabilities.md) — 能力词典（跨 backend 通用语义）
- [docs/connectors.md](docs/connectors.md) — Backend + Source 连接层
- [docs/backend-driver.md](docs/backend-driver.md) — Driver 怎么由你本地 agent 生成
- [docs/playbook-vs-skill-boundary.md](docs/playbook-vs-skill-boundary.md) — 贡献 playbook 前必读
- [docs/example-onboarding-transcript.md](docs/example-onboarding-transcript.md) — 真实 Onboarding 全程对话记录

---

## 贡献

最稀缺的贡献：

1. **新 playbook**——你的角色（财务 / 客服 / 法务 / 投研 / 教育 …）没有专属 playbook，把经验沉淀成 PR。写之前请先读 [docs/playbook-vs-skill-boundary.md](docs/playbook-vs-skill-boundary.md)。
2. **Skill 提交 Registry**——PR 改 [skills.json](skills.json) 加一条。
3. **Backend driver 范本**——把你本地 `commando connect` 生成的 driver 清理一下 PR 回来。
4. **新 agent CLI 适配**——`commando/runtime/llm.py` 里加 codex / kimi / glm / qwen / doubao / minimax 的 verified 命令格式（目前是 stub，社区欢迎补完）。

**不需要的贡献**：自建 GUI / 新增 Runtime 抽象 / 和某个 SaaS 深度绑定。这些违反 commando 设计原则。

---

## 当前阶段坦诚说

**已发**：CLI 全套 8 个子命令、Onboarding skill、go-live 一条龙、launchd 调度、双后端 LLM、Feishu IM 推送、本地 dashboard、LeMingle 真实样例。

**还在打磨**：Skill Registry（`commando install @author/skill` 现是 stub）、Linux systemd timer 模板、其他 agent CLI 的 verified 命令格式。

**短期不做**：GUI / SaaS / 多租户。

---

## License

[MIT](LICENSE) — Frank PU.

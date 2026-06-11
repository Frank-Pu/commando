# docs/ — commando 框架文档导航

> **这里所有文档都是关于 commando 框架本身**——讲框架的概念、协议、贡献
> 规则。**这里没有任何具体 agent 的 Configuration**。
>
> 想看真实的 agent Configuration 长什么样：
> - 参考实例 → [`examples/lemingle-growth-partner/`](../examples/lemingle-growth-partner/)
> - Onboarding 测试产物 → [`my-agent/`](../my-agent/)（建议 0.x 之后从 git 删除）

## 概念 Spec（"X 是什么"）

每篇讲一个 commando 的核心物件——读完你就知道这个物件在 Configuration
里长什么样、谁写、谁读、什么时候用。

| 文件 | 主题 | 谁该读 |
|---|---|---|
| [charter.md](charter.md) | 数字员工的宪法（身份/产品/ICP/红线 + 三档密度） | 写 Configuration 的人 |
| [scheduler.md](scheduler.md) | 产品表面（一张表两种 row + 4 种视图） | 写 schedule.yaml / 理解产品 UX 的人 |
| [skill.md](skill.md) | Skill 格式（Claude Code Skills + commando 扩展） | 写 / 复用 / 贡献 Skill 的人 |
| [memory.md](memory.md) | 三层记忆 Working / Episodic / Semantic + 与 Charter 的边界 | 设计长程 agent / 写 Reflection 的人 |

## 底层机制 Spec（"框架内部怎么转"）

跨 backend / 跨 platform 的协议层——做"接入 + 跨平台 + 工程实现"必读。

| 文件 | 主题 | 谁该读 |
|---|---|---|
| [capabilities.md](capabilities.md) | 能力词典：8 个域 + 跨 backend 语义 + native 逃生舱口 | 写 Skill / 贡献 backend / 想跨 backend 用 Configuration 的人 |
| [connectors.md](connectors.md) | Connector 概念：Backend vs Source + connectors.yaml 格式 | 配 connectors / 接数据源的人 |
| [backend-driver.md](backend-driver.md) | Driver 怎么由用户本地 agent 生成 + 生成 prompt 模板 | 跑 `commando connect <X>` / 贡献社区参考 driver 的人 |

## Contributor 原则

| 文件 | 主题 | 谁该读 |
|---|---|---|
| [playbook-vs-skill-boundary.md](playbook-vs-skill-boundary.md) | **playbook 与 SKILL.md 的内容边界**——commando 最关键的能力边界认知 | **准备 PR playbook 的人必读** |

## 教学素材 / Demo

| 文件 | 主题 | 谁该读 |
|---|---|---|
| [example-onboarding-transcript.md](example-onboarding-transcript.md) | commando 第一次 Onboarding dry-run 的完整对话记录 + 设计 commentary + 回流 todo 应用情况 | 想理解 Onboarding 实际怎么工作 / 想看 commando 设计如何被现实验证的人 |

---

## 命名一致性约定（容易混淆，值得说明）

某些名字在 commando 仓库的不同位置出现，**指代不同的东西**——这是
故意的命名一致性（让你看 example 时知道"对应 spec 里那篇 charter.md"）。

| 名字 | 在 docs/ 下 | 在 examples/ 或 my-agent/ 下 |
|---|---|---|
| `charter.md` | **关于 Charter 的 spec** | 一份具体的 Charter 实例 |
| `scheduler.md` / `schedule.yaml` | 关于 Scheduler 的 spec | 一份具体的 Schedule 配置 |
| `skill.md` / `SKILL.md` | 关于 Skill 格式的 spec | 一份具体的 Skill 实现（大写） |
| `connectors.md` / `connectors.yaml` | 关于 Connector 的 spec | 一份具体 Configuration 的 connector 配置 |

简单记忆：**docs/ 下小写讲概念，example/agent 目录下的 yaml/SKILL.md 是实例**。

---

*这份导航本身的目标：让你扫一眼就知道每个文档为谁服务，不用 cat 每个文件
猜内容。*

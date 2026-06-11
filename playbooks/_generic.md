# Playbook: Generic（兜底 playbook）

> 当 Role Scoping 阶段没匹配到具体 playbook 时加载这一份。
> **不要满足于跑通 generic**——跑完之后**强烈建议**用户把这次 Onboarding
> 的经验贡献回 commando 仓库，PR 一份新 playbook。

## 这份 playbook 的态度

不假装懂用户的领域。**少给推荐，多问问题**，把领域知识压力让用户自己承担。
产物的 Configuration 会偏粗糙，但能跑——重点是用户**真跑 2 周**之后
Re-onboarding 时会自然产出领域知识，那时候才有材料抽象成 playbook。

---

## Discovery 阶段：6 个通用维度

通用问法（详见主 SKILL.md 的 Discovery 节）。生硬地按顺序问，每个维度
2-3 个追问就转下一个，**不要在用户回答模糊时假装懂**——直接记到笔记里
留 Re-onboarding 解决。

---

## Calibration 阶段：通用决议

- **边界**：这个数字员工**做什么 + 不做什么**——必须画明确边界
- **核心方法论**：用户领域里的"标准工作流"是什么？让用户教你
- **任务节奏**：每天的"开机 / 交付 / 复盘"三个时点
- **Skill 启用清单**：基于用户描述的工作流，问 Registry 是否有可 import
- **Workbench backend**：用户现成在用什么协作工具，就选什么

每个决议都**先问"你们这个行业一般怎么做"**，再以此为基础给推荐。
不知道就说不知道——这是 generic 的诚实。

---

## 红线（必须写进 Charter，无论什么领域）

- 工作流硬 Gate：所有"对外发布 / 对第三方发送 / 不可逆操作"必须用户点确认
- AIGC 输出二次手改要求（如果对外发布）
- 敏感话题：政治 / 医疗 / 金融 / 未成年——任何命中直接 reject
- 隐私：不主动收集和外泄 PII

---

## 退出时一定要说的话

> 这次跑的是 generic playbook，所以 v0.1 Configuration 会比专属 playbook
> 粗一些。**建议你跑 2 周后**，把"哪些 Skill 真用了 / 哪些设计是错的 /
> 你的行业有哪些通用模式"整理一下，**PR 回 commando 仓库**做成一份
> 专属 playbook——下一个跟你做同行的 commando 用户会感谢你。

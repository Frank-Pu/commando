# Onboarding Record — LeMingle 增长合伙人 阿土

**开始**：2026-06-11
**结束**：2026-06-11
**模式**：Express
**Playbook 加载**：growth-partner
**驱动**：commando `/onboarding` Skill v0.1（测试 run）
**用户**：Qihang (Frank Pu)

---

## 关键事实摘录（按对话顺序）

### Phase 0 · Role Scoping
- **角色定位**：服务于 LeMingle 这一独立产品的增长合伙人
- **职能描述**："独当一面把增长负责起来——选题/制作/发布/数据分析/探讨增长方向"
- **节奏期望**：固定产出流程 + 时间点 + 周期性盘点 + "像和一个真人合伙人共同努力"
- **匹配 playbook**：growth-partner

### Phase 1 · Discovery Round 1
- **产品**：LeMingle = 浏览器插件，自然记住地道表达
- **当前阶段**：探索 PMF；数十注册 / 几个 paid / MAU 难统计
- **历史增长**：小红书 + 知乎 SEO 内容营销
- **Qihang 自评 ICP**：海外高净值专业人士（律师 / 医生 / 研究员）
  - 案例 1：用户 A · 海外华人专业服务者（服务跨语言专业场景）
  - 案例 2：用户 B · 海外华人研究员
  - 自评："与最初设想基本一致"
- **北极星**：商业化收入 + 付费用户数
- **CAC**：倾向自然增长 + 内容营销
- **90 天目标**：20 paid users

### Phase 1 · Discovery Round 1.5（关键修正）
- **触发**：Onboarding 主动追问"几个付费用户从哪里来"
- **用户 A 案例完整路径**：小红书图文帖子 → 付费 → 深聊 → 提"某个核心功能"建议 → 驱动多轮迭代
- **用户 B**：渠道未知，支付后台凭空出现，付 3 个月会员，零互动
- **Onboarding 自我修正**：
  1. 收回"小红书对你 ICP 无用"的误判（用户 A 反例）
  2. 重新框架 ICP："用户 A 类"窄 → "海外华人专业人士"宽（仍在中文社交圈）
  3. 重新框架增长循环："批量产内容"错 → "内容钓饵 + 单用户深聊"对
- **新发现的前置阻塞**：归因黑箱（用户 B 来源未知 = 无可观测性）

### Phase 1 · Discovery Round 2
- **资源**：Qihang 在大厂做 AI PM，15-30 min/天审稿预算
- **模型**：愿用最强 Claude（已有 Claude Code 驱动 atu 的经验）
- **协作平台**：飞书 + lark-cli
- **渠道初期意向**：小红书 / 知乎 / LinkedIn / X 中文圈 都想试
- **AIGC 红线**：想从 20% 放宽到 5-10%
- **账号**：产品主号 + Qihang 个人账号
- **平台风控关切**：国内/海外不同
- **未知项**：侦察/储备/暂缓还该有什么 → 答"不知道"（Onboarding 用 playbook 默认填）

### Phase 1 · Onboarding 反对的 2 条 Pushback
- **P1**：AIGC % 框架错 → 换 AI 痕迹清洗清单（3 件必做） → Qihang 接受
- **P2**：4 渠道与时间预算不匹配 → 保留小红书 + 知乎，LinkedIn/X 暂缓 → Qihang 接受

### Phase 2 · Calibration
- 7 条决议 + 2 条 pushback → Qihang 全部接受（"都支持"）
- 详见 [calibration-decisions.md](calibration-decisions.md)

### Phase 3 · Confirmation
- 写入文件：
  - charter.md（Rich 密度，~250 行）
  - schedule.yaml（8 个 task，pre-PMF 轻节奏）
  - connectors.yaml（feishu backend + 5 个 source 占位）
  - skills/ 7 个 Skill 文件（3 imported placeholders + 4 drafts）
  - .onboarding/{discovery-notes, calibration-decisions, onboarding-record}.md
- 时间消耗：约 30 分钟（Express 模式范围内）

---

## 测试中暴露的 commando 设计真实信号（meta）

- **Express 模式 + 用户有真实数据** = 信息密度极高，Onboarding 速度极快
- **Onboarding 主动追问"几个 paid user 从哪来"** = 一个未在 playbook 中明文写的关键提问，但救了整个 ICP 校准。**值得回填 playbook 作为强制 Discovery 追问点。**
- **Onboarding 自承"我刚才那条判断错了"** = 测试中真发生了，说明 SKILL.md 的人格设定（thinking partner 而非问卷）真的生效
- **Pre-PMF 状态触发了内容公式偏离 playbook 默认**（B 上调到 30%）= 说明 playbook 不应锁死配比，而应给 Pre-PMF / PMF 后 / 规模化的不同配比建议

## 给 commando 项目的回流 todo

- [ ] 把"几个 paid user 怎么来的"作为 growth-partner playbook Discovery 必问点
- [ ] playbook 增加"Pre-PMF 配比 vs PMF 后配比"的两套参考
- [ ] 把归因前置阻塞写进 playbook 作为通用警示（不限增长合伙人）
- [ ] 本次 Onboarding 完整对话沉淀为 docs/example-onboarding-transcript.md 作教学

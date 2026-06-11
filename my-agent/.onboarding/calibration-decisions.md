# Calibration Decisions — LeMingle 增长合伙人

**时间**：2026-06-11
**模式**：Express
**Playbook**：growth-partner
**用户拍板**：Qihang（全部 7 条 + 2 条 pushback 均接受）

---

## Pushback Accepted（Discovery 阶段就处理掉的）

### P1 · AIGC "X% 修改率"红线被打回
- **原方案**：playbook 默认 20% / 用户提议放宽到 5-10%
- **Onboarding 反对理由**：% 是错的框架，5-10% 几乎一定是 cosmetic 修改不能去 AI 痕迹
- **最终方案**：**AI 痕迹清洗清单**（3 件必做：清套话 transition / 加个人声音 / 删空泛形容词）替代 %
- **Qihang 拍板**：接受

### P2 · 4 渠道并行不可行
- **原方案**：小红书 + 知乎 + LinkedIn + X 中文圈 全跑
- **Onboarding 反对理由**：15-30 min/天审稿预算只能撑 2 个真在跑的渠道；LinkedIn/X 冷启动成本高
- **最终方案**：保留小红书 主线 + 知乎 储备 SEO；LinkedIn/X 暂缓，待 5-10 paid user 后启用
- **Qihang 拍板**：接受

---

## 决议 1 · Structured Work 边界
- **决议**：内容供应链 + 用户研究支持（call-prep / debrief / feedback-curator）
- **理由**：Pre-PMF 阶段用户深聊是最高 ROI；偏离 playbook 默认（playbook 默认只做内容供应链）
- **不做**：自动发布（commando 全局红线）/ ad-hoc 产品讨论（Layer 3 默认全开）
- **Qihang 拍板**：✅

## 决议 2 · Charter 密度
- **决议**：Rich（~3000 字）
- **理由**：ad-hoc 对话重度依赖 + ICP 有律师案例需 anchor + 平台风控差异化要写
- **Qihang 拍板**：✅

## 决议 3 · 内容公式（偏离 playbook）
- **决议**：A. ICP-Bridge 50% / B. **用户案例放大 30%** ↑ / C. PLG 20%
- **理由**：Pre-PMF 阶段不追爆款（playbook 默认的"爆款复刻 30%"），追"让下一个律师/PhD 看到能自我识别"
- **Qihang 拍板**：✅

## 决议 4 · 渠道分层
- **决议**：
  - 主线：小红书 商业号（2/周）
  - 储备 SEO：知乎（1 长文/月）
  - 侦察：小红书 个人号（不定时，founder voice）
  - 储备-信息源：Reddit / HN / 外刊 RSS
  - 暂缓：LinkedIn / X 中文圈 / TikTok / YouTube
- **升级规则**：暂缓→侦察 = 累计 5-10 paid user
- **Qihang 拍板**：✅

## 决议 5 · 任务节奏（Pre-PMF 轻节奏）
- **决议**：见 schedule.yaml 的 8 个 task
- **总审稿耗时**：~25 min/周 + ~30 min/月（远低于 Qihang 15-30 min/天预算，留余量给 ad-hoc）
- **关键约束**：不要日发笔记
- **Qihang 拍板**：✅

## 决议 6 · Structured Skill 启用清单
- **决议**：
  - 从 Registry 占位导入（实际实现待 commando CLI 或手动 fetch）：
    - @frank-pu/reddit-source-mining
    - @frank-pu/xhs-bilingual-bridge
    - @frank-pu/marketing-kit（启用其中 marketing-effect-analysis + SEO-content-optimization）
  - 新增 draft（status: draft，等工程实现）：
    - outlet-rss-scan
    - user-feedback-curator
    - user-call-prep
    - user-call-debrief
- **Qihang 拍板**：✅

## 决议 7 · Workbench Backend + 红线明文化
- **决议**：
  - Backend：飞书
  - 红线写进 Charter 7 节，含：发布人审 / AI 痕迹清洗清单 / 营销密度 per-platform / 账号策略 / 平台风控差异化 / 数据真实性 / 复刻边界
- **Qihang 拍板**：✅

---

## Configuration 之外的前置事项（不属于决议，但必须 Qihang 处理）

🚨 **归因黑箱**：波兰 PhD 凭空在 Stripe 出现 = 当前无任何渠道归因。
- **Qihang 必须做**：装 Plausible / Umami；注册流加"你从哪知道我们的"；小红书/知乎链接打 UTM
- **影响**：归因装好之前，`weekly_data_review` 任务的归因部分会跑空
- **写进 README**：是的 ✓

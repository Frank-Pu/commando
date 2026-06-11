# Example: LeMingle 增长合伙人（阿土）

> 这是 commando 的**官方参考 Configuration**——一个跑了 6+ 个月的真实
> 数字员工配置，服务于 [LeMingle](https://lemingle.com)（一个多语种地道
> 表达高亮 Chrome 插件）的增长业务。

## 这是什么

阿土（atu）是 commando 项目的 dogfood。它**不是 commando 写出来的**——它
**先于** commando 存在，commando 反过来从阿土的设计经验中抽象出来。

但阿土的 Configuration（Charter / Schedule / Skills / Connectors）刚好和
commando spec 兼容。所以我们把它放在这里作为：

- 一份**真实存在、跑得通**的 Configuration 全景示例
- 新用户 Onboarding 完之后**对照看"成熟 Configuration 长什么样"**的参照
- 增长合伙人 playbook（[`playbooks/growth-partner.md`](../../playbooks/growth-partner.md)）
  里所有抽象建议的**具体落地版本**

## 包含哪些文件

| 文件 | 内容 | 行数 |
|---|---|---|
| [`charter.md`](charter.md) | 阿土的角色宪法 v1.0（**Rich 密度**——身份/产品/ICP/北极星/方法论/红线全有）| 441 |
| [`schedule.yaml`](schedule.yaml) | 阿土的任务时间表 v0.2（覆盖 morning-sense / xhs-bridge / 周报 / 月度 SEO 等 7-8 个 task）| 217 |

## 还没在这里的（请直接看 atu 仓库）

- **Skills 全文**——这里只放 Charter 和 Schedule，避免和上游 atu 反复同步。
  完整 Skill 看 [atu 仓库 configuration/skills/](https://github.com/Frank-Pu/atu/tree/main/configuration/skills)
- **Connectors 实现**——双 Feishu app / Reddit OAuth / Playwright 渲染等，
  详见 [atu 仓库 connectors/](https://github.com/Frank-Pu/atu/tree/main/connectors)
- **Runtime 代码**——atu 自带的 runtime，commando 未来会抽象通用版

## 如何阅读这个示例

按这个顺序读，最贴近 Onboarding 走完之后用户拿到的实际产物：

1. 先读 [`charter.md`](charter.md) 的 1-3 节（**身份 / 产品 / 真实 ICP**）——
   感受 Charter Rich 密度长什么样
2. 再读 charter.md 的"红线"章节——感受**对 ad-hoc 对话和发布门槛的硬约束
   怎么落到文字**
3. 再扫 [`schedule.yaml`](schedule.yaml) 全文——感受**一周 cron 节奏**怎么
   组织
4. 对照 [`playbooks/growth-partner.md`](../../playbooks/growth-partner.md) 的
   "决议 1-7"，看每一条建议在这个 Configuration 里**如何具体兑现**

## 与 atu 上游的关系

- atu 是 source of truth，commando examples/ 是定期同步的镜像
- atu 真要改了，先改 atu，验证一段时间再回流到这里
- 反过来，如果 commando spec 演化导致 atu 不兼容，atu 也会跟着改

## 不要把这当成"模板复制粘贴"

阿土的 Charter / Schedule 是**给 LeMingle 这个具体产品**调出来的。直接
copy-paste 到你的产品上不会 work——里面的 ICP、内容公式、CAC 红线、
渠道分层都是 LeMingle-specific 的实证产物，不是通用模板。

正确的使用方式是：**跑你自己的 commando onboard，得到你自己的 v0.1
Configuration，遇到不确定时回到这份 example 看"成熟版本是怎么处理这一块的"**。

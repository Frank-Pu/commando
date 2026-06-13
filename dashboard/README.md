# commando dashboard

> 一个 ~300 行 HTML + ~150 行 Python 的本地 dashboard。
> 跑 `python server.py`，浏览器自动开。**不需要登录、不需要联网（除了 CDN）**。
> 这是 commando 的"裸跑得通"层，给你在没接任何 backend 时也能看到数字员工的样子。

## 为什么这里要有一个 dashboard

commando 的设计是把 scheduler **物化到用户已在用的协作平台**（飞书 bitable
多视图 / Notion database / 等）。但首次跑、还没接 backend、或纯调试时，
用户需要一个**零依赖、零配置**的入口看到东西。

本地 dashboard 解决这件事：
- 你第一次 clone commando 仓库 → `python dashboard/server.py` → 看到一个真实可点的看板
- 它不和飞书 materialize 竞争，是它的预演

设计上故意做得**比 backend 物化看板简单**——没有协作、没有移动端、没有
评论。它是"工地"不是"展厅"。

## 怎么跑

```bash
cd commando/dashboard
python server.py
# 浏览器自动打开 http://127.0.0.1:7878
```

可选参数：

```bash
python server.py --agent-dir ../my-agent --port 7878 --no-browser
```

`--agent-dir` 指向哪个 Configuration 目录（默认 `../my-agent/`）。
不存在时落回 mock data，仍能跑。

## 文件结构

```
dashboard/
├── server.py        ~250 行 Python http.server，读 schedule.yaml + 服务静态文件
├── index.html       Alpine.js 驱动的单页 UI
├── app.js           视图状态 / i18n / theme 切换 / 审稿按钮 dispatcher
├── styles.css       设计 token（teal/coral/amber/gray）+ dark mode
├── mock-data/
│   ├── instances.json     mock 任务执行记录（无 backend 时用）
│   └── draft-xhs-tue.md   mock 草稿（"审稿"按钮跳进去能看到东西）
└── README.md
```

## 设计 token（teal + coral）

| 角色 | 颜色 | 出现在 |
|---|---|---|
| **Brand teal** | teal-50/600/800 | avatar / active tab / skill chip / Done / Tomorrow 时间戳 / live dot |
| **Interaction coral** | coral-50/400/800 | Waiting review 状态 / 审稿按钮 / Awaiting metric / Kanban Review |
| **Functional amber** | amber-50/600/800 | Running 状态 / Kanban WIP |
| **Neutral gray** | gray | Idle 状态 / Inbox / 元数据文本 |

**核心心智**：只有 coral 应该让用户起身做事；其他三色都是 informational。

## 三个 UI 控制点

右上角：

- **EN / 中**：i18n 切换，存 `localStorage.commando.lang`，默认按 `navigator.language`
- **主题图标**（display/sun/moon）：三态循环——auto / light / dark，存 `localStorage.commando.theme`
- **refresh** 圆圈：重新 fetch `/api/data`
- **settings** 齿轮：暂时占位（v0.1 没设置项）

## 审稿按钮（A 单按钮方案）

每条 instance 有 `artifact_uri` 字段。审稿按钮 click → `openArtifact()`：

- `file://` 开头 → 调 `/api/open?uri=...` → 服务端 `open <path>` 打开
  本地默认编辑器（VS Code / Cursor / Typora 等）
- `https://` 开头 → `window.open(uri, '_blank')` 浏览器新 tab 打开（飞书
  wiki 文档 / Notion 页面 / 等）

审完之后改 markdown frontmatter 的 `status: approved` 保存——commando
监听到变化自动翻转 Workbench 状态。详见 [`docs/scheduler.md`](../docs/scheduler.md)。

## 0.x 阶段尚未做的事

- Kanban / Calendar / Table 三个 tab 还是 empty state（v0.1 只渲染 Today
  视图，其他三个等真有更多数据再做）
- 没有"在 dashboard 内点击直接翻状态"——审稿全靠 markdown 文件 frontmatter
- 没有 websocket / live update —— 状态变化需要按 refresh
- 没有移动端响应式 —— 设计上 desktop only（移动端去飞书 bitable 看）

## 为什么用 Alpine.js + Tailwind CDN 而不是 React / Vue

- 零 build step —— `python server.py` 就跑
- 单文件 HTML 容易 fork 改
- ~15kb Alpine + Tabler icons CDN 比 React 30x 轻
- 这层不需要复杂状态管理 —— 全靠 fetch + Alpine 就够

如果将来需要 SSR / SEO / 复杂交互，可以重写。但 v0.1 目标是"裸跑得通"，
重型 framework 反而阻塞这个目标。

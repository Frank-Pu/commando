<p align="center">
  <img src="dashboard/ant.svg" alt="commando" width="100" />
</p>

# commando

> **Configure your own AI digital employee in 25 minutes.** It runs on whatever AI tool you already use — Claude Code, Cursor, Windsurf, Codex, Kimi, GLM, Qwen, Doubao, MiniMax, Gemini.

[中文 README →](README.zh-CN.md)

You spend 25 minutes in conversation with your AI tool. It produces `my-agent/` on disk — a Charter, a Schedule, a set of Skills. The OS scheduler runs them. The output lands in your existing Feishu / Notion / IM. **The agent is files you own**, not a SaaS you rent.

```bash
curl -fsSL https://raw.githubusercontent.com/Frank-Pu/commando/main/install.sh | sh
commando onboard         # 25-min dialog → ./my-agent/
commando build-skills    # fill in Skill prompt bodies
commando go-live         # connect IM + install schedule
```

Tomorrow at 8am, your digital employee fires its first task and pings you on IM.

---

## What does a digital employee look like?

Three real configurations to make it concrete:

### Growth Partner — Indie product creator's content + insight partner

> *Charter excerpt:* "I am [Product]'s growth partner. Voice: plain, data-first, never marketing-speak. Red lines: AIGC manual-edit ≥ 20%, zero outbound links on Xiaohongshu, marketing density ≤ 20%."

> *Schedule:* `morning_sense 08:00 daily` · `xhs_draft 11:00 Tue+Fri` · `weekly_data_review 16:00 Fri` · `weekly_reflection 19:00 Sun`

*Live for 6+ months serving [LeMingle](https://lemingle.com) — the canonical reference Configuration in this repo.*

### Personal Finance Advisor — Always-on watcher of your accounts

> *Charter excerpt:* "I am your personal finance advisor. Red lines: I never execute trades; I never predict markets; I never recommend high-risk products; my quarterly reports must include a section 'where I might be wrong'."

> *Schedule:* `daily_portfolio_health 07:00` · `monthly_tax_check 1st 09:00` · `quarterly_rebalance_review last-day-of-quarter`

### Job Search Coach — 3-month sprint partner for switching roles

> *Charter excerpt:* "I am your career-pivot coach. Voice: warm but no-water. Red lines: I won't pad your résumé; I won't help you dodge real weaknesses; if 3 months pass with no progress I will say so."

> *Schedule:* `daily_listing_scan 09:00` · `interview_debrief manual` · `weekly_pacing_check 19:00 Sun`

---

## Why commando over the alternatives?

|   | **commando** | ChatGPT / GPTs | LangChain / agent frameworks | Zapier + LLM |
|---|---|---|---|---|
| Your agent is yours to own | ✅ files in your repo | ❌ trapped on OpenAI | ✅ code in your repo | ❌ trapped on Zapier |
| Pick your own LLM | ✅ any (Claude / GLM / Kimi / …) | ❌ OpenAI only | ⚠️ each provider rewrites code | ⚠️ via integrations only |
| Schedule on your OS | ✅ launchd / systemd / cron | ❌ none | ⚠️ build yourself | ✅ (their cron) |
| Output goes to YOUR tools | ✅ Feishu / Notion / your IM | ❌ ChatGPT UI | ⚠️ build yourself | ✅ (their integrations) |
| Long-term memory you can read | ✅ markdown on disk | ⚠️ hidden context | ⚠️ vector DB you wire | ❌ no memory |
| Onboarding to get you started | ✅ 25-min dialog | ❌ DIY | ❌ DIY | ❌ DIY |

The pitch: **runtime is commodity, configuration is the moat**. We deliberately don't compete on Runtime — we make the Configuration shareable, versionable, and yours.

---

## How it works (the only mental model you need)

| Layer | What it is | Who runs it |
|---|---|---|
| **Charter** | Your agent's constitution — identity, voice, ICP, red lines. Auto-injected into every call. | `charter.md` you own |
| **Skills** | Discrete tasks the agent can perform (write a post, debrief a meeting). Activated by Schedule or IM. | `skills/*/SKILL.md` |
| **Schedule** | When to fire which Skills. Auto-translated to launchd / systemd. | `schedule.yaml` |

Ad-hoc dialogue ("can you help me think through X?") works automatically because the Charter is always loaded — no extra Skill needed.

---

## Install a community Skill, instantly

```bash
commando install @commando/daily-briefing       # morning briefing template
commando install @commando/meeting-debrief      # meeting → actions + Semantic memory
commando install @commando/competitive-watch    # weekly competitor diff
commando install https://github.com/…/SKILL.md  # any GitHub URL works
```

The Skill auto-rebuilds itself against YOUR Charter so its voice matches your agent.

---

## Status

Shipped: install + onboard + build-skills + go-live + schedule + Feishu IM + local dashboard + Registry (3 verified Skills). Validated through 3 rounds of stranger-onboarding dogfood.

Not yet: Linux `systemd` template (mac launchd works), more verified third-party agent CLIs, Stripe/Plausible KPI dashboard.

---

## Contributing

Most needed:
1. **Real Configurations from your domain** — finance, legal, ops, research, customer success. PR an `examples/<role>/` with charter + schedule (anonymized).
2. **Skills for `registry/`** — PR `registry/<skill-name>/SKILL.md` + an entry in `skills.json`.
3. **Verified backends** — pin down the exact `kimi` / `glm` / `qwen` / `doubao` CLI syntax in `commando/runtime/llm.py`.

## License

[MIT](LICENSE) — Frank PU.

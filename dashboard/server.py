#!/usr/bin/env python3
"""
commando dashboard server.

Reads ../my-agent/schedule.yaml + workbench/instances (or falls back to mock data)
and serves a single-file dashboard at http://localhost:7878.

Usage:
    python server.py [--agent-dir <path>] [--port 7878] [--no-browser]
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import urllib.parse
import webbrowser
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Timer
from typing import Optional

HERE = Path(__file__).resolve().parent
MOCK_DIR = HERE / "mock-data"


YAML_WARNED = False


def parse_yaml(path: Path) -> dict:
    """Load schedule.yaml via pyyaml if available; otherwise print a friendly
    warning and return {} so the dashboard falls back to mock data."""
    global YAML_WARNED
    try:
        import yaml  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        if not YAML_WARNED:
            sys.stderr.write(
                "note: pyyaml is not installed — dashboard will use mock data.\n"
                "      install with: pip install pyyaml\n"
            )
            YAML_WARNED = True
        return {}
    except Exception as e:
        sys.stderr.write(f"warning: failed to parse {path}: {e}\n")
        return {}


def load_agent(agent_dir: Path) -> dict:
    name = "agent"
    subtitle = ""
    charter = agent_dir / "charter.md"
    if charter.exists():
        text = charter.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# Charter:"):
                rest = line.replace("# Charter:", "").strip()
                if "·" in rest:
                    parts = [p.strip() for p in rest.split("·", 1)]
                    name, subtitle = parts[0], parts[1]
                else:
                    name = rest
                break
    avatar = name[:1] if name else "a"
    agent_key = agent_dir.name if agent_dir else "default"
    avatar_url = AVATAR_URLS.get(agent_key) or avatar_url_for(agent_key)
    return {"name": name, "subtitle": subtitle, "avatar": avatar, "avatar_url": avatar_url}


def load_schedule(agent_dir: Path) -> list:
    yml = agent_dir / "schedule.yaml"
    if not yml.exists():
        return []
    data = parse_yaml(yml)
    return data.get("tasks", []) if isinstance(data, dict) else []


def parse_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip()
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(block) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        result = {}
        for line in block.splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                result[k.strip()] = v.strip().strip('"').strip("'")
        return result


def load_skills(agent_dir: Path) -> list:
    skills_dir = agent_dir / "skills"
    if not skills_dir.exists() or not skills_dir.is_dir():
        return []
    skills = []
    for sub in sorted(skills_dir.iterdir()):
        if not sub.is_dir():
            continue
        md = sub / "SKILL.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md)
        desc = fm.get("description") or ""
        if isinstance(desc, str):
            desc = " ".join(desc.split())
        skills.append({
            "id": fm.get("name", sub.name),
            "dir": sub.name,
            "description": desc[:160] + ("…" if len(desc) > 160 else ""),
            "source": fm.get("source"),
            "status": fm.get("status", "active"),
            "playbooks": fm.get("playbooks") or [],
            "requires_human_approval": bool(fm.get("requires_human_approval")),
        })
    return skills


def cron_today(cron: str, today_dow: int, today_dom: int) -> bool:
    """Best-effort match: is this cron firing today? Supports '0 8 * * *' style."""
    if not cron:
        return False
    parts = cron.split()
    if len(parts) < 5:
        return False
    _, _, dom, _, dow = parts
    dow_match = dow == "*" or str(today_dow) in dow.split(",") or "-" in dow and _range_match(dow, today_dow)
    dom_match = dom == "*" or str(today_dom) in dom.split(",")
    if dow == "*" and dom == "*":
        return True
    if dow != "*" and dom != "*":
        return dow_match and dom_match
    if dow != "*":
        return dow_match
    return dom_match


def cron_time(cron: str) -> str:
    parts = (cron or "").split()
    if len(parts) < 2:
        return ""
    minute = parts[0].zfill(2)
    hour = parts[1].zfill(2)
    return f"{hour}:{minute}"


def _range_match(s: str, n: int) -> bool:
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                if int(a) <= n <= int(b):
                    return True
            except ValueError:
                pass
        else:
            try:
                if int(part) == n:
                    return True
            except ValueError:
                pass
    return False


def load_mock_instances() -> list:
    path = MOCK_DIR / "instances.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        instances = json.load(f)
    for inst in instances:
        uri = inst.get("artifact_uri")
        if uri and uri.startswith("file://./"):
            local = uri.replace("file://./", "", 1)
            abs_path = (HERE / local).resolve()
            inst["artifact_uri"] = "file://" + str(abs_path)
    return instances


DICEBEAR_STYLE = "personas"
AGENT_BACKGROUNDS = {
    "atu": "E1F5EE",     # teal-50
    "caiwa": "FAECE7",   # coral-50
}


def avatar_url_for(agent_id: str) -> str:
    bg = AGENT_BACKGROUNDS.get(agent_id, "E1F5EE")
    seed = agent_id or "default"
    return (f"https://api.dicebear.com/9.x/{DICEBEAR_STYLE}/svg"
            f"?seed={seed}&backgroundColor={bg}&radius=50")


AVATAR_URLS = {
    "atu":   avatar_url_for("atu"),
    "caiwa": avatar_url_for("caiwa"),
}


def discover_agents(root: Optional[Path], primary_dir: Path, multi_agent_mode: bool) -> list:
    if multi_agent_mode and root and root.exists() and root.is_dir():
        agents = []
        for sub in sorted(root.iterdir()):
            if sub.is_dir() and (sub / "charter.md").exists() and (sub / "schedule.yaml").exists():
                a = load_agent(sub)
                a["id"] = sub.name
                a["dir"] = str(sub)
                a["avatar_url"] = AVATAR_URLS.get(sub.name)
                agents.append(a)
        if agents:
            return agents
    primary = {"id": "atu", "dir": str(primary_dir), "avatar_url": AVATAR_URLS["atu"]}
    if primary_dir.exists() and (primary_dir / "charter.md").exists():
        primary.update(load_agent(primary_dir))
        primary["avatar_url"] = AVATAR_URLS["atu"]
    else:
        primary.update({"name": "阿土", "subtitle": "LeMingle 增长合伙人", "avatar": "阿"})
    secondary = {"id": "caiwa", "name": "财娃", "subtitle": "投研助手 · A 股 + 港股",
                 "avatar": "财", "avatar_url": AVATAR_URLS["caiwa"],
                 "dir": "(mock — v0.1 demo)"}
    return [primary, secondary]


def _mock_agents_meta() -> list:
    return [
        {"id": "atu", "name": "阿土", "subtitle": "LeMingle 增长合伙人", "avatar": "阿", "dir": "./my-agent"},
        {"id": "caiwa", "name": "财娃", "subtitle": "投研助手 · A 股 + 港股", "avatar": "财", "dir": "./agents/caiwa"},
    ]


def build_data(agent_dir: Path) -> dict:
    agent = load_agent(agent_dir)
    schedule = load_schedule(agent_dir)
    instances = load_mock_instances()
    skills = load_skills(agent_dir)

    runtime_data = agent_dir / "workbench" / "instances.jsonl"
    if not runtime_data.exists():
        return _attach_skills(_full_mock(agent), skills)

    if not schedule:
        return _attach_skills(_full_mock(agent), skills)

    today = date.today()
    tomorrow = today + timedelta(days=1)
    today_dow = (today.weekday() + 1) % 7
    tomorrow_dow = (tomorrow.weekday() + 1) % 7

    by_task = {}
    for inst in instances:
        by_task.setdefault(inst["task_id"], []).append(inst)

    today_tasks = []
    for task in schedule:
        if not task.get("enabled", True):
            continue
        trigger = task.get("trigger", {}) or {}
        cron = trigger.get("cron")
        ttype = trigger.get("type")
        if ttype == "cron" and cron and cron_today(cron, today_dow, today.day):
            latest = (by_task.get(task["id"]) or [None])[0]
            today_tasks.append(_format_task(task, latest))
        elif ttype == "manual":
            latest = (by_task.get(task["id"]) or [None])[0]
            if latest and latest.get("status") == "WaitingApproval":
                today_tasks.append(_format_task(task, latest))

    if not today_tasks:
        today_tasks = [_format_task(t, by_task.get(t.get("id"), [None])[0])
                       for t in _fallback_today_picks(schedule)]

    tomorrow_tasks = []
    for task in schedule:
        if not task.get("enabled", True):
            continue
        trigger = task.get("trigger", {}) or {}
        cron = trigger.get("cron")
        if cron and cron_today(cron, tomorrow_dow, tomorrow.day):
            tomorrow_tasks.append({
                "id": task["id"],
                "task_id": task["id"],
                "time": cron_time(cron),
            })

    if len(tomorrow_tasks) < 3:
        for task in schedule:
            trigger = task.get("trigger", {}) or {}
            if trigger.get("type") == "manual":
                tomorrow_tasks.append({
                    "id": task["id"] + "-manual",
                    "task_id": task["id"],
                    "time": "—",
                })
            if len(tomorrow_tasks) >= 4:
                break

    metrics = {
        "awaiting": sum(1 for t in today_tasks if t.get("status") == "WaitingApproval"),
        "running": sum(1 for t in today_tasks if t.get("status") in ("Running", "WIP")),
        "done_today": sum(1 for t in today_tasks if t.get("status") == "Done"),
        "this_week": len([t for t in schedule if t.get("enabled", True)]),
    }

    kanban = _rich_kanban()
    week = compute_week(schedule, today)
    month = compute_month(schedule, today)

    # v2: flat task list for Schedule tab (raw schedule.yaml shape + flags)
    all_tasks = []
    for t in schedule:
        trig = t.get("trigger") or {}
        all_tasks.append({
            "id": t.get("id"),
            "name": t.get("name", ""),
            "enabled": t.get("enabled", True),
            "cron": trig.get("cron"),
            "trigger_type": trig.get("type", "cron"),
            "skills": t.get("skills") or [],
            "tags": t.get("tags") or [],
        })

    return _attach_skills({
        "agent": agent,
        "metrics": metrics,
        "today": {
            "date": today.isoformat(),
            "tasks": today_tasks,
        },
        "tomorrow": {
            "date": tomorrow.isoformat(),
            "tasks": tomorrow_tasks[:4] if tomorrow_tasks else [],
        },
        "kanban": kanban,
        "week": week,
        "month": month,
        "tasks": all_tasks,
        "knowledge": _knowledge_growth_partner(),
        "activity": _mock_activity_atu(today),
    }, skills)


def _mock_activity_atu(today: date) -> dict:
    base = datetime.now().astimezone()
    def at(hour, minute, second=0, day_offset=0):
        ref = base.replace(hour=hour, minute=minute, second=second, microsecond=0)
        return (ref - timedelta(days=day_offset)).isoformat()

    events = [
        {"ts": at(14, 23, 7), "level": "im", "skill": "xhs-bilingual-bridge",
         "task_id": "xhs_draft_tue",
         "message": "IM @ Qihang: 「今天选题里这条值得看一下 → reddit.com/r/languagelearning/...」"},
        {"ts": at(14, 21, 55), "level": "done", "skill": "marketing-effect-analysis",
         "task_id": "weekly_data_review", "message": "7 张图已生成 · weekly-data-report.md 已写", "duration_ms": 89000},
        {"ts": at(14, 18, 42), "level": "running", "skill": "marketing-effect-analysis",
         "task_id": "weekly_data_review", "message": "调用 marketing-effect-analysis · 89%"},
        {"ts": at(14, 17, 11), "level": "running", "skill": "marketing-effect-analysis",
         "task_id": "weekly_data_review", "message": "抓 plausible.io 数据 · 7 天窗口"},
        {"ts": at(14, 16, 22), "level": "running", "skill": "marketing-effect-analysis",
         "task_id": "weekly_data_review", "message": "抓 xhs_data · 商业号 + 个人号"},
        {"ts": at(14, 15, 0), "level": "trigger", "task_id": "weekly_data_review",
         "message": "cron 0 16 * * 5 · weekly_data_review"},
        {"ts": at(13, 50, 11), "level": "idle", "message": "等待下一个 trigger · next: 14:15 weekly_data_review"},
        {"ts": at(11, 30, 8), "level": "im", "task_id": "xhs_draft_tue",
         "message": "IM @ Qihang: 「xhs_draft_tue 等你审稿 · 审稿 checklist 见 docx 末」"},
        {"ts": at(11, 2, 34), "level": "waiting", "skill": "xhs-bilingual-bridge",
         "task_id": "xhs_draft_tue", "message": "artifact 已提交飞书 docx · 等你审稿", "duration_ms": 107000},
        {"ts": at(11, 1, 47), "level": "done", "skill": "xhs-bilingual-bridge",
         "task_id": "xhs_draft_tue", "message": "slide_plan.json + 12 张图占位 · CHECKLIST.md 写好"},
        {"ts": at(11, 0, 59), "level": "running", "skill": "xhs-bilingual-bridge",
         "task_id": "xhs_draft_tue", "message": "Bridge 公式 A · 写第 5 / 5 段"},
        {"ts": at(10, 59, 14), "level": "running", "skill": "xhs-bilingual-bridge",
         "task_id": "xhs_draft_tue", "message": "Bridge 公式 A · 写第 3 / 5 段"},
        {"ts": at(10, 58, 22), "level": "running", "skill": "xhs-bilingual-bridge",
         "task_id": "xhs_draft_tue", "message": '从选题池取 1 条 · "How I learn idioms passively" (score 4.3)'},
        {"ts": at(11, 0, 0), "level": "trigger", "task_id": "xhs_draft_tue",
         "message": "cron 0 11 * * 2 · xhs_draft_tue"},
        {"ts": at(10, 33, 8), "level": "done", "skill": "user-call-prep",
         "task_id": "user_call_prep", "message": "5 问已草稿 · call-prep-userC.md 写好 · 推 IM 提醒",
         "duration_ms": 116000},
        {"ts": at(10, 31, 22), "level": "running", "skill": "user-call-prep",
         "task_id": "user_call_prep", "message": "WebFetch LinkedIn · 拉历史 IM 对话"},
        {"ts": at(10, 30, 55), "level": "trigger", "task_id": "user_call_prep",
         "message": "manual · IM Qihang: 「明天 14:30 我跟用户 C 聊」"},
        {"ts": at(9, 47, 13), "level": "im",
         "message": "IM @ Qihang: 「Reddit 12 条选题已入库 · 看看哪条做今天的稿」"},
        {"ts": at(8, 2, 22), "level": "done", "skill": "reddit-source-mining",
         "task_id": "morning_sense", "message": "12 candidates · score >= 4 · 写入选题池",
         "duration_ms": 142000},
        {"ts": at(8, 1, 48), "level": "running", "skill": "reddit-source-mining",
         "task_id": "morning_sense", "message": "LLM 4 维打分 · 47 / 47 条"},
        {"ts": at(8, 0, 14), "level": "running", "skill": "reddit-source-mining",
         "task_id": "morning_sense", "message": "抓 r/IWantToLearn · top 24h · 12 条候选"},
        {"ts": at(8, 0, 11), "level": "running", "skill": "reddit-source-mining",
         "task_id": "morning_sense", "message": "抓 r/ChineseLanguage · top 24h · 8 条候选"},
        {"ts": at(8, 0, 8), "level": "running", "skill": "reddit-source-mining",
         "task_id": "morning_sense", "message": "抓 r/LearnEnglish · top 24h · 14 条候选"},
        {"ts": at(8, 0, 3), "level": "running", "skill": "reddit-source-mining",
         "task_id": "morning_sense", "message": "抓 r/languagelearning · top 24h · 13 条候选"},
        {"ts": at(8, 0, 0), "level": "trigger", "task_id": "morning_sense",
         "message": "cron 0 8 * * * · morning_sense"},
        {"ts": at(19, 0, 14, day_offset=1), "level": "done", "skill": "user-feedback-curator",
         "task_id": "weekly_reflection",
         "message": "Semantic memory: content-formula-performance.md 已更新", "duration_ms": 67000},
        {"ts": at(19, 0, 0, day_offset=1), "level": "trigger", "task_id": "weekly_reflection",
         "message": "cron 0 19 * * 0 · weekly_reflection"},
        {"ts": at(16, 30, 22, day_offset=2), "level": "done", "skill": "user-call-debrief",
         "task_id": "user_call_debrief", "message": "用户 A debrief 5 条 insight · user-quote-vault.md 追加 3 条"},
    ]
    seeds = [
        {"level": "im", "message": "IM @ Qihang: 「今天的复盘做完了，重点 3 条」"},
        {"level": "running", "skill": "reddit-source-mining", "message": "扫描中 · r/ChineseLanguage · 已处理 8 / 24"},
        {"level": "trigger", "task_id": "morning_sense", "message": "cron 0 8 * * * · 准备启动"},
        {"level": "idle", "message": "等待下一个 trigger"},
        {"level": "done", "skill": "outlet-rss-scan", "message": "外刊 RSS 已扫 · 6 条入选 (Economist 3 / NYT 2 / Aeon 1)", "duration_ms": 18000},
        {"level": "running", "skill": "marketing-effect-analysis", "message": "对账 stripe 后台 · 抓近 7 天 paid signup 5 条"},
        {"level": "im", "message": "IM @ Qihang: 「波兰那位 paid user 今天又登了一次，看要不要主动联系」"},
        {"level": "waiting", "skill": "xhs-bilingual-bridge", "task_id": "xhs_draft_fri", "message": "新稿已提交 · 等你审"},
    ]
    return {"events": events, "live_seeds": seeds}


def _mock_activity_caiwa() -> dict:
    base = datetime.now().astimezone()
    def at(hour, minute, second=0):
        return base.replace(hour=hour, minute=minute, second=second, microsecond=0).isoformat()

    events = [
        {"ts": at(14, 0, 8), "level": "im", "skill": "earnings-fetcher",
         "task_id": "earnings_check",
         "message": "IM @ Qihang: 「BYD 25Q4 营收低于一致预期 2.3% · brief 已写，待你审」"},
        {"ts": at(13, 58, 12), "level": "waiting", "skill": "earnings-fetcher",
         "task_id": "earnings_check", "message": "比亚迪 25Q4 brief · artifact 已提交 · 等你审稿"},
        {"ts": at(13, 56, 44), "level": "done", "skill": "earnings-fetcher",
         "task_id": "earnings_check", "message": "BYD 关键差异已标注: 毛利率 -1.8pp / 海外销量 +28%",
         "duration_ms": 92000},
        {"ts": at(13, 55, 0), "level": "trigger", "task_id": "earnings_check",
         "message": "manual · 港股盘后 BYD 财报发布"},
        {"ts": at(10, 31, 0), "level": "done", "skill": "sector-rotation-scan",
         "task_id": "sector_rotation_scan",
         "message": "28 个申万一级行业资金流已扫 · 异常: 电力设备 +1.8σ", "duration_ms": 44000},
        {"ts": at(10, 30, 0), "level": "trigger", "task_id": "sector_rotation_scan",
         "message": "cron 30 10 * * 1-5"},
        {"ts": at(9, 16, 33), "level": "done", "skill": "a-share-scan",
         "task_id": "market_open_brief", "message": "12 holdings brief · 比亚迪 / 宁德 / 拼多多 重点关注",
         "duration_ms": 87000},
        {"ts": at(9, 15, 0), "level": "trigger", "task_id": "market_open_brief",
         "message": "cron 15 9 * * 1-5"},
        {"ts": at(7, 30, 22), "level": "done", "skill": "us-overnight-recap",
         "task_id": "us_overnight", "message": "NVDA +2.1% · BABA +0.8% · 中概股 ADR 整体偏强",
         "duration_ms": 41000},
        {"ts": at(7, 30, 0), "level": "trigger", "task_id": "us_overnight",
         "message": "cron 30 7 * * 1-5"},
    ]
    seeds = [
        {"level": "running", "skill": "a-share-scan", "message": "扫沪深通净流入 · 北向 +12.4 亿"},
        {"level": "im", "message": "IM @ Qihang: 「比亚迪 25Q4 数据全 → DCF 模型更新中」"},
        {"level": "done", "skill": "valuation-model", "message": "比亚迪 DCF 2026 估值刷新 · 目标价 ¥420", "duration_ms": 52000},
        {"level": "trigger", "task_id": "market_open_brief", "message": "cron 15 9 * * 1-5"},
        {"level": "idle", "message": "盘前等待 · next: 09:15 market_open_brief"},
    ]
    return {"events": events, "live_seeds": seeds}


def _knowledge_growth_partner() -> list:
    return [
        {
            "id": "drafts",
            "name_zh": "内容草稿",
            "name_en": "Content drafts",
            "icon": "ti-file-text",
            "backend": "Feishu Wiki · 📝 内容初稿",
            "backend_url": "https://feishu.cn/wiki/...",
            "count": 14,
            "items": [
                {"title": "xhs_draft_tue · circle back", "updated_zh": "2 小时前", "updated_en": "2 hours ago", "url": "#"},
                {"title": "xhs_draft_fri · in a nutshell", "updated_zh": "昨天", "updated_en": "yesterday", "url": "#"},
                {"title": "zhihu_monthly_seo · LeMingle vs Trancy", "updated_zh": "上周一", "updated_en": "last Mon", "url": "#"},
            ],
        },
        {
            "id": "research",
            "name_zh": "用户研究",
            "name_en": "User research",
            "icon": "ti-users",
            "backend": "Feishu Wiki · 用户访谈",
            "backend_url": "https://feishu.cn/wiki/...",
            "count": 6,
            "items": [
                {"title": "call-debrief · 用户 A (美国华人律师)", "updated_zh": "前天", "updated_en": "2 days ago", "url": "#"},
                {"title": "call-prep · 用户 C (海外医生)", "updated_zh": "草稿", "updated_en": "draft", "url": "#"},
                {"title": "user-quote-vault.md", "updated_zh": "周日", "updated_en": "Sunday", "url": "#"},
            ],
        },
        {
            "id": "reflection",
            "name_zh": "数据复盘",
            "name_en": "Data review",
            "icon": "ti-chart-line",
            "backend": "Feishu Wiki · 复盘报告",
            "backend_url": "https://feishu.cn/wiki/...",
            "count": 9,
            "items": [
                {"title": "weekly-reflection · 2026-W24", "updated_zh": "本周日", "updated_en": "this Sun", "url": "#"},
                {"title": "weekly-data-report · 2026-W23", "updated_zh": "上周五", "updated_en": "last Fri", "url": "#"},
                {"title": "channel-conversion-curves.md", "updated_zh": "周日反思更新", "updated_en": "updated Sun", "url": "#"},
            ],
        },
        {
            "id": "pool",
            "name_zh": "选题池",
            "name_en": "Topic pool",
            "icon": "ti-database",
            "backend": "Feishu Bitable · 选题池",
            "backend_url": "https://feishu.cn/base/...",
            "count": 42,
            "items": [
                {"title": "How I learn idioms passively · 4.3", "updated_zh": "今早 08:01", "updated_en": "08:01 today", "url": "#"},
                {"title": '"circle back" overuse in tech · 4.1', "updated_zh": "今早 08:01", "updated_en": "08:01 today", "url": "#"},
                {"title": "in a nutshell origin · 3.8", "updated_zh": "今早 08:01", "updated_en": "08:01 today", "url": "#"},
            ],
        },
        {
            "id": "semantic",
            "name_zh": "Semantic Memory",
            "name_en": "Semantic memory",
            "icon": "ti-brain",
            "backend": "Local · semantic/*.md",
            "backend_url": "#",
            "count": 5,
            "items": [
                {"title": "content-formula-performance.md", "updated_zh": "上周更新", "updated_en": "last week", "url": "#"},
                {"title": "icp-refinements.md", "updated_zh": "2 周前", "updated_en": "2 weeks ago", "url": "#"},
                {"title": "what-doesnt-work.md", "updated_zh": "3 周前", "updated_en": "3 weeks ago", "url": "#"},
            ],
        },
    ]


def _knowledge_finance_analyst() -> list:
    return [
        {
            "id": "company-profile",
            "name_zh": "公司画像",
            "name_en": "Company profiles",
            "icon": "ti-building-skyscraper",
            "backend": "Feishu Wiki · 公司库",
            "backend_url": "#",
            "count": 87,
            "items": [
                {"title": "比亚迪 (002594) · 25Q4 update", "updated_zh": "今早", "updated_en": "today", "url": "#"},
                {"title": "Pinduoduo (PDD) · earnings deep-dive", "updated_zh": "昨天", "updated_en": "yesterday", "url": "#"},
                {"title": "Nvidia (NVDA) · valuation refresh", "updated_zh": "前天", "updated_en": "2 days ago", "url": "#"},
            ],
        },
        {
            "id": "sector",
            "name_zh": "行业研报",
            "name_en": "Sector research",
            "icon": "ti-chart-pie",
            "backend": "Feishu Wiki · 行业",
            "backend_url": "#",
            "count": 23,
            "items": [
                {"title": "新能源车产业链 · 2026 H1", "updated_zh": "本周三", "updated_en": "Wed", "url": "#"},
                {"title": "半导体设备 · 国产替代追踪", "updated_zh": "上周", "updated_en": "last week", "url": "#"},
                {"title": "AI infra 海外巨头季度对比", "updated_zh": "上周", "updated_en": "last week", "url": "#"},
            ],
        },
        {
            "id": "valuation",
            "name_zh": "估值模型",
            "name_en": "Valuation models",
            "icon": "ti-calculator",
            "backend": "Feishu Sheets · DCF 模型库",
            "backend_url": "#",
            "count": 35,
            "items": [
                {"title": "比亚迪 DCF (2026-2030)", "updated_zh": "今早", "updated_en": "today", "url": "#"},
                {"title": "宁德时代 multi-stage DCF", "updated_zh": "昨天", "updated_en": "yesterday", "url": "#"},
                {"title": "可比公司估值矩阵 · 新能源", "updated_zh": "本周二", "updated_en": "Tue", "url": "#"},
            ],
        },
        {
            "id": "earnings",
            "name_zh": "财报追踪",
            "name_en": "Earnings tracker",
            "icon": "ti-calendar-event",
            "backend": "Feishu Bitable · 财报日历",
            "backend_url": "#",
            "count": 18,
            "items": [
                {"title": "本周财报 · 6 家科技股", "updated_zh": "周一更新", "updated_en": "Mon update", "url": "#"},
                {"title": "下周财报预告 · 关注 8 家", "updated_zh": "今天", "updated_en": "today", "url": "#"},
                {"title": "上季度业绩 vs 预期偏差汇总", "updated_zh": "本周三", "updated_en": "Wed", "url": "#"},
            ],
        },
    ]


def compute_week(schedule: list, today: date) -> dict:
    monday = today - timedelta(days=today.weekday())
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        dow = (d.weekday() + 1) % 7
        tasks = []
        for task in schedule:
            if not task.get("enabled", True):
                continue
            trigger = task.get("trigger", {}) or {}
            cron = trigger.get("cron")
            if cron and cron_today(cron, dow, d.day):
                tasks.append({"time": cron_time(cron), "task_id": task["id"]})
        tasks.sort(key=lambda x: x["time"])
        days.append({
            "date": d.isoformat(),
            "weekday": d.weekday(),
            "dom": f"{d.month}/{d.day}",
            "is_today": d == today,
            "tasks": tasks,
        })
    sunday = monday + timedelta(days=6)
    label = f"{monday.month}/{monday.day} — {sunday.month}/{sunday.day}"
    return {"start": monday.isoformat(), "label": label, "days": days}


def _rich_kanban() -> dict:
    return {
        "inbox": [
            {"title": "How I learn idioms passively", "meta": "score 4.3 · r/languagelearning"},
            {"title": '"circle back" overuse in tech', "meta": "score 4.1 · The Atlantic"},
            {"title": "in a nutshell origin", "meta": "score 3.8 · Aeon"},
            {"title": "海外留学群体痛点访谈", "meta": "score 3.7 · founder note"},
        ],
        "wip": [
            {"title": "xhs_draft_tue", "meta": "started 11:02", "skill": "xhs-bilingual-bridge"},
        ],
        "review": [
            {"title": "xhs_draft_tue · circle back note", "meta": "done 11:02 · 等你审稿",
             "actionable": True, "artifact_uri": None, "skill": "xhs-bilingual-bridge"},
        ],
        "done": [
            {"title": "morning_sense", "meta": "08:00 · 12 picked", "skill": "reddit-source-mining"},
            {"title": "user_call_debrief · 用户 A", "meta": "yesterday 16:30", "skill": "user-call-debrief"},
            {"title": "weekly_reflection", "meta": "Sun 19:00", "skill": "user-feedback-curator"},
            {"title": "outlet-rss-scan", "meta": "today 08:01", "skill": "outlet-rss-scan"},
        ],
    }


def _attach_skills(data: dict, skills: list) -> dict:
    data["skills"] = skills or _mock_skills()
    return data


def _mock_skills() -> list:
    return [
        {"id": "reddit-source-mining", "dir": "reddit-source-mining",
         "description": "扫指定 subreddit 拉 top 候选帖 + LLM 4 维打分，写入选题池",
         "source": "@frank-pu/reddit-source-mining@planned",
         "status": "imported-placeholder", "playbooks": ["growth-partner"], "requires_human_approval": False},
        {"id": "xhs-bilingual-bridge", "dir": "xhs-bilingual-bridge",
         "description": "把 Reddit/HN 优质讨论加工成小红书 Bilingual Bridge 图文",
         "source": "@frank-pu/xhs-bilingual-bridge@planned",
         "status": "imported-placeholder", "playbooks": ["growth-partner"], "requires_human_approval": True},
        {"id": "marketing-kit", "dir": "marketing-kit",
         "description": "8 件套通用营销 Skill bundle（营销文案 / 效果分析 / 竞品追踪 等）",
         "source": "@frank-pu/marketing-kit@planned",
         "status": "imported-placeholder", "playbooks": ["growth-partner"], "requires_human_approval": False},
        {"id": "outlet-rss-scan", "dir": "outlet-rss-scan",
         "description": "每日扫外刊 RSS，提取地道表达密度高的片段进选题池",
         "source": None, "status": "draft", "playbooks": ["growth-partner"], "requires_human_approval": False},
        {"id": "user-feedback-curator", "dir": "user-feedback-curator",
         "description": "把 IM/邮件/小红书评论里的用户反馈系统化沉淀到 Semantic Memory",
         "source": None, "status": "draft", "playbooks": ["growth-partner"], "requires_human_approval": False},
        {"id": "user-call-prep", "dir": "user-call-prep",
         "description": "用户访谈前 prep — 读 LinkedIn / 历史交互 / Semantic 起草 5 问",
         "source": None, "status": "draft", "playbooks": ["growth-partner"], "requires_human_approval": False},
        {"id": "user-call-debrief", "dir": "user-call-debrief",
         "description": "用户访谈后 debrief — 把口述内容提炼成 insights，进 Semantic Memory",
         "source": None, "status": "draft", "playbooks": ["growth-partner"], "requires_human_approval": False},
    ]


def _format_task(task: dict, instance: Optional[dict]) -> dict:
    status = (instance or {}).get("status") or ("Manual" if task.get("trigger", {}).get("type") == "manual" else "Idle")
    skills = task.get("skills") or []
    summary = (instance or {}).get("summary") or _default_summary(task, status)
    return {
        "id": (instance or {}).get("id") or task["id"],
        "task_id": task["id"],
        "skills": skills,
        "status": status,
        "summary": summary,
        "artifact_uri": (instance or {}).get("artifact_uri"),
        "workbench_uri": (instance or {}).get("workbench_uri"),
    }


def _default_summary(task: dict, status: str) -> str:
    trig = task.get("trigger", {}) or {}
    if trig.get("type") == "manual":
        return "Manual · IM trigger ready"
    return f"{cron_time(trig.get('cron', ''))} scheduled"


def _full_mock(agent: dict) -> dict:
    today = date.today()
    default_agent = {"name": "阿土", "subtitle": "LeMingle 增长合伙人", "avatar": "阿", "avatar_url": AVATAR_URLS["atu"]}
    resolved = agent if agent.get("name") != "agent" else default_agent
    if "avatar_url" not in resolved:
        resolved["avatar_url"] = AVATAR_URLS.get("atu")
    # v2: include flat tasks for Schedule tab even in mock fallback
    mock_tasks = []
    try:
        # Try to read real schedule.yaml if it exists (gives toggle ability)
        real_dir = HERE.parent / "my-agent"
        if (real_dir / "schedule.yaml").exists():
            for t in load_schedule(real_dir):
                trig = t.get("trigger") or {}
                mock_tasks.append({
                    "id": t.get("id"),
                    "name": t.get("name", ""),
                    "enabled": t.get("enabled", True),
                    "cron": trig.get("cron"),
                    "trigger_type": trig.get("type", "cron"),
                    "skills": t.get("skills") or [],
                    "tags": t.get("tags") or [],
                })
    except Exception:
        pass
    return {
        "agent": resolved,
        "tasks": mock_tasks,
        "metrics": {"awaiting": 1, "running": 2, "done_today": 4, "this_week": 9},
        "today": {
            "date": today.isoformat(),
            "tasks": [
                {"id": "morning_sense-1", "task_id": "morning_sense",
                 "skills": ["reddit-source-mining", "outlet-rss-scan"],
                 "status": "Done", "summary": "08:00 ran · 12 candidates · 142s",
                 "artifact_uri": None, "workbench_uri": None},
                {"id": "xhs_draft_tue-1", "task_id": "xhs_draft_tue",
                 "skills": ["xhs-bilingual-bridge"],
                 "status": "WaitingApproval",
                 "summary": "11:00 ran · 1 笔记初稿 · 等你审稿",
                 "artifact_uri": "file://" + str((MOCK_DIR / "draft-xhs-tue.md").resolve()),
                 "workbench_uri": None},
                {"id": "user_call_prep-idle", "task_id": "user_call_prep",
                 "skills": ["user-call-prep"],
                 "status": "Manual", "summary": "Manual · IM trigger ready",
                 "artifact_uri": None, "workbench_uri": None},
            ],
        },
        "tomorrow": {
            "date": (today + timedelta(days=1)).isoformat(),
            "tasks": [
                {"id": "t1", "task_id": "morning_sense", "time": "08:00"},
                {"id": "t2", "task_id": "xhs_draft_thu", "time": "11:00"},
                {"id": "t3", "task_id": "user_call_prep", "time": "14:30"},
                {"id": "t4", "task_id": "daily_journal", "time": "17:00"},
            ],
        },
        "kanban": _rich_kanban(),
        "week": _mock_week(today),
        "month": _mock_month(today),
        "knowledge": _knowledge_growth_partner(),
        "activity": _mock_activity_atu(today),
    }


def build_mock_for_agent(agent_id: str) -> dict:
    today = date.today()
    if agent_id == "caiwa":
        agent = {"name": "财娃", "subtitle": "投研助手 · A 股 + 港股", "avatar": "财",
                 "avatar_url": AVATAR_URLS["caiwa"]}
        return {
            "agent": agent,
            "metrics": {"awaiting": 2, "running": 1, "done_today": 6, "this_week": 14},
            "today": {"date": today.isoformat(), "tasks": [
                {"id": "ms-1", "task_id": "market_open_brief", "skills": ["a-share-scan", "us-overnight-recap"],
                 "status": "Done", "summary": "09:15 · briefed 12 holdings · 87s", "artifact_uri": None},
                {"id": "ec-1", "task_id": "earnings_check", "skills": ["earnings-fetcher"],
                 "status": "WaitingApproval", "summary": "比亚迪 25Q4 · 关键差异已标注 · 等你 review",
                 "artifact_uri": None},
                {"id": "vw-1", "task_id": "valuation_watch", "skills": ["valuation-model"],
                 "status": "Manual", "summary": "Manual · 你想看哪只在 IM 说", "artifact_uri": None},
            ]},
            "tomorrow": {"date": (today + timedelta(days=1)).isoformat(), "tasks": [
                {"id": "t1", "task_id": "market_open_brief", "time": "09:15"},
                {"id": "t2", "task_id": "sector_rotation_scan", "time": "10:30"},
                {"id": "t3", "task_id": "earnings_check", "time": "14:00"},
                {"id": "t4", "task_id": "daily_journal", "time": "16:30"},
            ]},
            "kanban": {
                "inbox": [
                    {"title": "AI infra Q1 catch-up", "meta": "tag: macro"},
                    {"title": "Pinduoduo Temu margin debate", "meta": "tag: deep-dive"},
                ],
                "wip": [{"title": "earnings_check · BYD", "meta": "started 13:55"}],
                "review": [{"title": "earnings_check · BYD 25Q4 brief", "meta": "等你审稿"}],
                "done": [
                    {"title": "market_open_brief", "meta": "09:15 · 12 holdings"},
                    {"title": "us-overnight-recap", "meta": "07:30 · NVDA +2.1%"},
                    {"title": "valuation_watch · CATL", "meta": "yesterday"},
                ],
            },
            "week": _mock_week(today),
            "month": _mock_month(today),
            "knowledge": _knowledge_finance_analyst(),
            "activity": _mock_activity_caiwa(),
            "skills": _mock_skills_finance(),
        }
    # default: atu / growth-partner
    return _full_mock({"name": "阿土", "subtitle": "LeMingle 增长合伙人", "avatar": "阿"})


def _mock_skills_finance() -> list:
    return [
        {"id": "a-share-scan", "dir": "a-share-scan",
         "description": "盘前扫 A 股核心持仓 + 板块异动 + 沪深通净流向",
         "status": "imported-placeholder", "playbooks": ["finance-analyst"], "requires_human_approval": False,
         "source": "@frank-pu/a-share-scan@planned"},
        {"id": "us-overnight-recap", "dir": "us-overnight-recap",
         "description": "美股隔夜要闻 + 中概股 ADR 表现 + 美联储动向",
         "status": "imported-placeholder", "playbooks": ["finance-analyst"], "requires_human_approval": False,
         "source": "@frank-pu/us-overnight-recap@planned"},
        {"id": "earnings-fetcher", "dir": "earnings-fetcher",
         "description": "财报发布日自动拉关键数据 + 与一致预期对比 + 写差异分析草稿",
         "status": "imported-placeholder", "playbooks": ["finance-analyst"], "requires_human_approval": True,
         "source": "@frank-pu/earnings-fetcher@planned"},
        {"id": "valuation-model", "dir": "valuation-model",
         "description": "DCF / 可比公司多模型估值 · 输出敏感性矩阵",
         "status": "draft", "playbooks": ["finance-analyst"], "requires_human_approval": True,
         "source": None},
        {"id": "sector-rotation-scan", "dir": "sector-rotation-scan",
         "description": "每日扫 28 个申万一级行业资金流 + 涨跌幅 · 标异常",
         "status": "draft", "playbooks": ["finance-analyst"], "requires_human_approval": False,
         "source": None},
    ]


def _mock_week(today: date) -> dict:
    monday = today - timedelta(days=today.weekday())
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        tasks = [{"time": t, "task_id": tid} for t, tid in _mock_day_tasks(d.weekday())]
        days.append({
            "date": d.isoformat(),
            "weekday": d.weekday(),
            "dom": f"{d.month}/{d.day}",
            "is_today": d == today,
            "tasks": tasks,
        })
    sunday = monday + timedelta(days=6)
    return {
        "start": monday.isoformat(),
        "label": f"{monday.month}/{monday.day} — {sunday.month}/{sunday.day}",
        "days": days,
    }


def _mock_day_tasks(weekday: int) -> list:
    by_day = {
        0: [("08:00", "morning_sense")],
        1: [("08:00", "morning_sense"), ("11:00", "xhs_draft_tue")],
        2: [("08:00", "morning_sense"), ("14:30", "user_call_prep")],
        3: [("08:00", "morning_sense")],
        4: [("08:00", "morning_sense"), ("11:00", "xhs_draft_fri"), ("16:00", "weekly_data_review")],
        5: [("08:00", "morning_sense")],
        6: [("08:00", "morning_sense"), ("19:00", "weekly_reflection")],
    }
    return by_day.get(weekday, [])


def compute_month(schedule: list, today: date) -> dict:
    first = today.replace(day=1)
    grid_start = first - timedelta(days=(first.weekday() + 1) % 7)
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    weeks = []
    cur = grid_start
    for _ in range(6):
        week_days = []
        for _ in range(7):
            dow = (cur.weekday() + 1) % 7
            in_month = cur.month == today.month and cur.year == today.year
            tasks = []
            if schedule:
                for task in schedule:
                    if not task.get("enabled", True):
                        continue
                    trigger = task.get("trigger", {}) or {}
                    cron = trigger.get("cron")
                    if cron and cron_today(cron, dow, cur.day):
                        tasks.append({"time": cron_time(cron), "task_id": task["id"]})
                tasks.sort(key=lambda x: x["time"])
            else:
                tasks = [{"time": t, "task_id": tid} for t, tid in _mock_day_tasks(cur.weekday())]
            week_days.append({
                "date": cur.isoformat(),
                "dom": cur.day,
                "in_month": in_month,
                "is_today": cur == today,
                "tasks": tasks,
            })
            cur = cur + timedelta(days=1)
        weeks.append({"days": week_days})
        if cur >= next_first and cur.weekday() == 6:
            break
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    return {
        "label": f"{today.year} {month_names[today.month - 1]}",
        "month_zh": f"{today.year} 年 {today.month} 月",
        "weeks": weeks,
    }


def _mock_month(today: date) -> dict:
    return compute_month([], today)


def _fallback_today_picks(schedule: list) -> list:
    picks = []
    for task in schedule:
        if not task.get("enabled", True):
            continue
        trigger = task.get("trigger", {}) or {}
        if trigger.get("type") in ("cron", "manual"):
            picks.append(task)
        if len(picks) >= 3:
            break
    return picks


def open_local_path(uri: str) -> bool:
    if not uri.startswith("file://"):
        return False
    path = urllib.parse.unquote(uri.replace("file://", "", 1))
    if not Path(path).exists():
        return False
    try:
        sys_name = platform.system()
        if sys_name == "Darwin":
            subprocess.Popen(["open", path])
        elif sys_name == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# v2 dashboard helpers — Skills impact / Charter edit / Schedule toggle /
#                       Install / Connectors / Semantic memory
# ──────────────────────────────────────────────────────────────────────────────

def read_charter(agent_dir: Path) -> dict:
    p = agent_dir / "charter.md"
    if not p.exists():
        return {"ok": False, "error": f"charter.md not found at {p}"}
    return {"ok": True, "path": str(p), "text": p.read_text(encoding="utf-8"),
            "bytes": p.stat().st_size}


def write_charter(agent_dir: Path, text: str) -> dict:
    p = agent_dir / "charter.md"
    if not p.parent.exists():
        return {"ok": False, "error": f"{p.parent} does not exist"}
    # atomic-ish: write to temp, rename
    tmp = p.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(p)
    return {"ok": True, "bytes": p.stat().st_size}


def compute_skill_stats(agent_dir: Path) -> list:
    """For each skill, compute fires in last 30 days from episodic events."""
    skills_dir = agent_dir / "skills"
    epdir = agent_dir / "memory" / "episodic"

    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    by_name = {}
    for sp in skill_files:
        fm = parse_frontmatter(sp)
        name = fm.get("name") or sp.parent.name
        by_name[name] = {
            "name": name,
            "status": fm.get("status", "draft"),
            "description": fm.get("description", "") or "",
            "tags": fm.get("tags") or [],
            "source": fm.get("source") or "",
            "fires_30d": 0,
            "done_30d": 0,
            "fail_30d": 0,
            "last_fire": None,
            "path": str(sp),
        }

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    if epdir.exists():
        for log in sorted(epdir.glob("*.jsonl")):
            try:
                for line in log.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    skill = ev.get("skill")
                    if not skill or skill not in by_name:
                        continue
                    ts = ev.get("ts", "")
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                    if dt < cutoff:
                        continue
                    level = ev.get("level") or ""
                    if level == "trigger":
                        by_name[skill]["fires_30d"] += 1
                        cur = by_name[skill]["last_fire"]
                        if not cur or ts > cur:
                            by_name[skill]["last_fire"] = ts
                    elif level == "done":
                        by_name[skill]["done_30d"] += 1
                    elif level in ("fail", "error"):
                        by_name[skill]["fail_30d"] += 1
            except Exception:
                continue

    return list(by_name.values())


def toggle_task_in_schedule(agent_dir: Path, task_id: str, enabled: bool) -> dict:
    """Find `- id: X` block in schedule.yaml, toggle `enabled: true/false`.
    Preserves comments and structure by doing text-level edit."""
    p = agent_dir / "schedule.yaml"
    if not p.exists():
        return {"ok": False, "error": f"schedule.yaml not found at {p}"}
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")

    in_task = False
    found = False
    desired_str = "true" if enabled else "false"
    out = []
    for i, line in enumerate(lines):
        s = line.strip()
        # detect task header
        if s.startswith("- id:") and s.split(":", 1)[1].strip() == task_id:
            in_task = True
            found = True
            out.append(line)
            continue
        # next task starts → exit
        if in_task and s.startswith("- id:") and s.split(":", 1)[1].strip() != task_id:
            in_task = False
        if in_task and s.startswith("enabled:"):
            # preserve indent
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f"{indent}enabled: {desired_str}")
            in_task = False  # done with this task
            continue
        out.append(line)

    if not found:
        return {"ok": False, "error": f"task '{task_id}' not found in schedule.yaml"}

    tmp = p.with_suffix(".yaml.tmp")
    tmp.write_text("\n".join(out), encoding="utf-8")
    tmp.replace(p)
    return {"ok": True, "task": task_id, "enabled": enabled}


def install_skill(source: str, agent_dir: Path) -> dict:
    """Wrap `commando install <source>` as a subprocess and return output."""
    if not source or len(source) > 1000:
        return {"ok": False, "error": "invalid source"}
    # Locate the commando module — same repo as this dashboard
    repo_root = HERE.parent
    cmd = [sys.executable, "-m", "commando.cli", "install",
           source, "--agent-dir", str(agent_dir), "-y",
           "--no-rebuild", "--no-schedule"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                           cwd=str(repo_root))
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "install timed out (60s)"}
    return {
        "ok": r.returncode == 0,
        "stdout": r.stdout[-4000:],
        "stderr": r.stderr[-2000:],
        "returncode": r.returncode,
    }


def read_connectors_status(agent_dir: Path) -> dict:
    """Return connector health: which credentials files exist, which are configured."""
    out = {"connectors": []}
    cred_dir = agent_dir / "credentials"
    known = [
        ("feishu",   "Feishu IM",      "notify_chat_id"),
        ("obsidian", "Obsidian vault", "vault_path"),
        ("anthropic", "Anthropic API", "api_key"),
        ("notion",   "Notion",         "api_key"),
        ("stripe",   "Stripe",         "api_key"),
        ("slack",    "Slack",          "webhook_url"),
    ]
    for slug, label, key in known:
        cred_file = cred_dir / f"{slug}.yaml"
        if cred_file.exists():
            data = parse_yaml(cred_file)
            # Look anywhere in the parsed YAML for the key
            present = key in (data or {}) or any(
                isinstance(v, dict) and key in v for v in (data or {}).values()
            )
            out["connectors"].append({
                "slug": slug, "label": label, "status": "ok" if present else "partial",
                "configured": present, "path": str(cred_file),
            })
        else:
            out["connectors"].append({
                "slug": slug, "label": label, "status": "missing",
                "configured": False, "path": str(cred_file),
            })
    return out


def read_semantic_memory(agent_dir: Path) -> list:
    """List files in memory/semantic/ with a preview."""
    sem_dir = agent_dir / "memory" / "semantic"
    out = []
    if not sem_dir.exists():
        return out
    for p in sorted(sem_dir.glob("*.md")):
        try:
            text = p.read_text(encoding="utf-8")
            title = next((ln.strip("# ").strip() for ln in text.splitlines() if ln.startswith("#")), p.stem)
            preview = "\n".join(text.splitlines()[:8])
            out.append({"file": p.name, "title": title, "preview": preview,
                        "bytes": p.stat().st_size, "path": str(p)})
        except Exception:
            continue
    return out


def make_handler(agent_dir: Path, agents_root: Optional[Path]):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/agents":
                agents = discover_agents(agents_root, agent_dir, multi_agent_mode=agents_root is not None)
                return self._json({"agents": agents, "active_id": agents[0]["id"] if agents else None})
            if parsed.path == "/api/data":
                qs = urllib.parse.parse_qs(parsed.query)
                agent_id = (qs.get("agent") or [""])[0]
                if agent_id and agent_id != "atu":
                    return self._json(build_mock_for_agent(agent_id))
                return self._json(build_data(agent_dir))
            if parsed.path == "/api/open":
                qs = urllib.parse.parse_qs(parsed.query)
                uri = (qs.get("uri") or [""])[0]
                ok = open_local_path(uri)
                return self._json({"ok": ok})
            # v2 read endpoints
            if parsed.path == "/api/charter":
                return self._json(read_charter(agent_dir))
            if parsed.path == "/api/skill-stats":
                return self._json({"skills": compute_skill_stats(agent_dir)})
            if parsed.path == "/api/connectors":
                return self._json(read_connectors_status(agent_dir))
            if parsed.path == "/api/semantic":
                return self._json({"items": read_semantic_memory(agent_dir)})
            return self._static(parsed.path)

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            try:
                raw = self.rfile.read(length) if length else b""
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception as e:
                return self._error(400, f"bad JSON: {e}")

            if parsed.path == "/api/charter":
                text = body.get("text", "")
                if not isinstance(text, str) or len(text) > 200_000:
                    return self._error(400, "invalid text")
                return self._json(write_charter(agent_dir, text))

            if parsed.path == "/api/task-toggle":
                task_id = body.get("task")
                enabled = bool(body.get("enabled"))
                if not task_id:
                    return self._error(400, "task id required")
                return self._json(toggle_task_in_schedule(agent_dir, task_id, enabled))

            if parsed.path == "/api/install":
                source = body.get("source", "")
                if not source:
                    return self._error(400, "source required")
                return self._json(install_skill(source, agent_dir))

            return self._error(404, "not found")

        def _static(self, path: str):
            if path == "/" or path == "":
                target = HERE / "index.html"
            else:
                rel = path.lstrip("/").split("?")[0]
                target = (HERE / rel).resolve()
                if HERE not in target.parents and target != HERE:
                    return self._error(403, "forbidden")
            if not target.exists() or target.is_dir():
                return self._error(404, "not found")
            ctype = self._ctype(target.suffix)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(target.read_bytes())

        def _json(self, obj):
            payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def _error(self, code, msg):
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg.encode("utf-8"))

        def _ctype(self, suffix):
            return {
                ".html": "text/html; charset=utf-8",
                ".css":  "text/css; charset=utf-8",
                ".js":   "text/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".md":   "text/markdown; charset=utf-8",
                ".svg":  "image/svg+xml",
                ".png":  "image/png",
                ".ico":  "image/x-icon",
            }.get(suffix.lower(), "application/octet-stream")

        def log_message(self, fmt, *args):
            sys.stderr.write(f"[{self.address_string()}] {fmt % args}\n")

    return Handler


def main():
    p = argparse.ArgumentParser(prog="commando-dashboard")
    p.add_argument("--agent-dir", default=str(HERE.parent / "my-agent"),
                   help="Path to active Configuration directory")
    p.add_argument("--agents-root", default=None,
                   help="Optional: root dir holding multiple agent subdirs (multi-agent mode)")
    p.add_argument("--port", type=int, default=7878)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    agent_dir = Path(args.agent_dir).resolve()
    agents_root = Path(args.agents_root).resolve() if args.agents_root else None
    if not agent_dir.exists():
        sys.stderr.write(f"warning: agent dir {agent_dir} does not exist — using mock data only\n")

    handler = make_handler(agent_dir, agents_root)
    server = HTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}"
    sys.stderr.write(f"commando dashboard running at {url}\n")
    sys.stderr.write(f"reading from: {agent_dir}\n")

    if not args.no_browser:
        Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\nshutting down\n")


if __name__ == "__main__":
    main()

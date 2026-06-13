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
from datetime import date, datetime, timedelta
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
    return {"name": name, "subtitle": subtitle, "avatar": avatar}


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
    }, skills)


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
    return {
        "agent": agent if agent.get("name") != "agent" else {"name": "阿土", "subtitle": "LeMingle 增长合伙人", "avatar": "阿"},
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
    }


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


def make_handler(agent_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/data":
                return self._json(build_data(agent_dir))
            if parsed.path == "/api/open":
                qs = urllib.parse.parse_qs(parsed.query)
                uri = (qs.get("uri") or [""])[0]
                ok = open_local_path(uri)
                return self._json({"ok": ok})
            return self._static(parsed.path)

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
                   help="Path to Configuration directory (default: ../my-agent/)")
    p.add_argument("--port", type=int, default=7878)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    agent_dir = Path(args.agent_dir).resolve()
    if not agent_dir.exists():
        sys.stderr.write(f"warning: agent dir {agent_dir} does not exist — using mock data only\n")

    handler = make_handler(agent_dir)
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

"""commando status — one-glance health snapshot."""

import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import click

from commando.schedule_install import (
    _load_schedule,
    parse_simple_cron,
    next_firing,
    _format_next_firing,
)


def _ok(label: str) -> str:
    return click.style("  ✓  ", fg="green") + label


def _bad(label: str) -> str:
    return click.style("  ✗  ", fg="red") + label


def _dim(label: str) -> str:
    return click.style("  ·  ", fg="bright_black") + label


def run(target: str) -> None:
    agent_dir = Path(target).resolve()

    click.echo()
    click.secho(f"  commando status  ({agent_dir.name})", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()

    # ── Configuration ────────────────────────────────────────────────────────
    click.secho("  Configuration", bold=True)
    charter = agent_dir / "charter.md"
    click.echo(_ok(f"charter.md  ({charter.stat().st_size} bytes)") if charter.exists()
               else _bad("charter.md missing — run `commando onboard`"))

    skills = sorted((agent_dir / "skills").glob("*/SKILL.md")) if (agent_dir / "skills").exists() else []
    active = [s for s in skills if "status: active" in s.read_text(encoding="utf-8", errors="ignore")]
    click.echo(_ok(f"skills: {len(skills)} total, {len(active)} active"))
    for s in active[:5]:
        click.echo(_dim(s.parent.name))
    if len(active) > 5:
        click.echo(_dim(f"… and {len(active) - 5} more"))

    schedule = _load_schedule(agent_dir)
    tasks = schedule.get("tasks") or []
    cron_tasks = [t for t in tasks if (t.get("trigger") or {}).get("type") == "cron"]
    manual_tasks = [t for t in tasks if (t.get("trigger") or {}).get("type") == "manual"]
    click.echo(_ok(f"schedule.yaml: {len(cron_tasks)} cron, {len(manual_tasks)} manual") if tasks
               else _bad("schedule.yaml missing or empty"))

    # ── LLM backend ──────────────────────────────────────────────────────────
    click.echo()
    click.secho("  LLM backend (Runtime is commodity)", bold=True)
    found_cli = None
    for binary, name in [("claude", "Claude Code"), ("codex", "Codex"),
                          ("kimi", "Kimi"), ("glm", "GLM"), ("qwen", "Qwen"),
                          ("doubao", "Doubao"), ("minimax", "MiniMax")]:
        if shutil.which(binary):
            found_cli = (binary, name)
            break
    if found_cli:
        click.echo(_ok(f"agent CLI: {found_cli[1]} ({shutil.which(found_cli[0])})"))
    else:
        click.echo(_bad("no agent CLI in PATH"))
    if os.environ.get("ANTHROPIC_API_KEY"):
        click.echo(_ok("ANTHROPIC_API_KEY set (headless cron fallback available)"))
    elif (agent_dir / "credentials" / "anthropic.yaml").exists():
        click.echo(_ok("credentials/anthropic.yaml present (headless cron fallback)"))

    # ── Connectors ───────────────────────────────────────────────────────────
    click.echo()
    click.secho("  Connectors", bold=True)
    feishu = agent_dir / "credentials" / "feishu.yaml"
    if feishu.exists():
        click.echo(_ok(f"Feishu IM: {feishu}"))
    else:
        click.echo(_bad("Feishu IM not configured — run `commando connect im-feishu`"))

    # ── OS scheduler ─────────────────────────────────────────────────────────
    click.echo()
    click.secho("  OS scheduler", bold=True)
    if platform.system() != "Darwin":
        click.echo(_dim(f"non-Darwin ({platform.system()}) — manual systemd/Task Scheduler"))
    else:
        prefix = f"commando.{agent_dir.name}."
        plist_dir = Path.home() / "Library" / "LaunchAgents"
        installed = sorted(plist_dir.glob(f"{prefix}*.plist")) if plist_dir.exists() else []
        if not installed:
            click.echo(_bad(f"no launchd jobs installed — run `commando schedule install --apply`"))
        else:
            click.echo(_ok(f"{len(installed)} launchd job(s) installed"))

            # Compute upcoming firings across all cron tasks
            upcoming = []
            for t in cron_tasks:
                cron = (t.get("trigger") or {}).get("cron")
                parsed = parse_simple_cron(cron) if cron else None
                if parsed:
                    nxt = next_firing(parsed)
                    if nxt:
                        upcoming.append((nxt, t["id"]))
            upcoming.sort()
            if upcoming:
                click.echo()
                click.echo("  Upcoming firings:")
                for dt, tid in upcoming[:5]:
                    click.echo(_dim(f"{dt:%a %b %d %H:%M}  {tid}"))

    # ── Recent activity ──────────────────────────────────────────────────────
    click.echo()
    click.secho("  Recent activity (episodic memory)", bold=True)
    today = datetime.now().strftime("%Y-%m-%d")
    today_log = agent_dir / "memory" / "episodic" / f"{today}.jsonl"
    if not today_log.exists():
        click.echo(_dim("no events today yet"))
    else:
        lines = today_log.read_text(encoding="utf-8").strip().split("\n")
        click.echo(_ok(f"{len(lines)} event(s) today"))
        for line in lines[-3:]:
            import json
            try:
                e = json.loads(line)
                ts = e.get("ts", "?")[:19].replace("T", " ")
                kind = e.get("level") or e.get("kind") or e.get("type") or "?"
                skill = e.get("skill") or e.get("task_id") or e.get("task") or ""
                click.echo(_dim(f"{ts}  {kind:<12} {skill}"))
            except Exception:
                pass

    click.echo()

"""commando schedule — translate schedule.yaml into OS scheduler entries.

macOS  → ~/Library/LaunchAgents/commando.<agent>.<task>.plist (launchd)
Linux  → printed systemd timer + service templates (manual install for now)
Windows → printed schtasks recommendations (manual)

This is the realization of: "Onboarding produces schedule.yaml → OS drives execution".
We don't write our own daemon — the OS already has a great one.
"""

import os
import platform
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click


# ──────────────────────────────────────────────────────────────────────────────
# cron parsing (minimal — single values only; ranges/steps rejected for v0.2)
# ──────────────────────────────────────────────────────────────────────────────

def parse_simple_cron(expr: str) -> Optional[dict]:
    """Parse a SIMPLE 5-field cron expr. Returns dict with int values or None for '*'.
    Returns None if expression uses ranges/steps/lists (v0.2 rejects)."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return None
    keys = ["minute", "hour", "day", "month", "weekday"]
    out = {}
    for k, p in zip(keys, parts):
        if p == "*":
            out[k] = None
        elif p.isdigit():
            out[k] = int(p)
        else:
            return None  # ranges/lists/steps unsupported in v0.2
    return out


# ──────────────────────────────────────────────────────────────────────────────
# macOS launchd
# ──────────────────────────────────────────────────────────────────────────────

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python}</string>
    <string>-m</string>
    <string>commando.cli</string>
    <string>run</string>
    <string>--task</string>
    <string>{task_id}</string>
    <string>--agent-dir</string>
    <string>{agent_dir}</string>
    <string>--apply</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{repo_dir}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>{path_env}</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
{calendar_interval}
  </dict>
  <key>StandardOutPath</key>
  <string>{log_dir}/{task_id}.out.log</string>
  <key>StandardErrorPath</key>
  <string>{log_dir}/{task_id}.err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
"""


def _py_weekday_from_cron(cron_dow: int) -> int:
    """cron: 0=Sun, 1=Mon..6=Sat (also 7=Sun). python: Mon=0..Sun=6."""
    if cron_dow == 7:
        cron_dow = 0
    return (cron_dow - 1) % 7


def next_firing(parsed: dict, now: Optional[datetime] = None) -> Optional[datetime]:
    """Iterate forward minute by minute (max 31 days) to find next firing."""
    now = now or datetime.now()
    candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 31):
        m, h, d, mo, w = (parsed.get(k) for k in ("minute", "hour", "day", "month", "weekday"))
        if (m is None or candidate.minute == m) \
           and (h is None or candidate.hour == h) \
           and (d is None or candidate.day == d) \
           and (mo is None or candidate.month == mo) \
           and (w is None or candidate.weekday() == _py_weekday_from_cron(w)):
            return candidate
        candidate += timedelta(minutes=1)
    return None


def _format_next_firing(dt: Optional[datetime]) -> str:
    if dt is None:
        return "  (next firing > 31 days away — check cron expression)"
    delta = dt - datetime.now()
    if delta.total_seconds() < 60:
        rel = "in <1 min"
    elif delta.days >= 1:
        rel = f"in {delta.days}d {delta.seconds // 3600}h"
    elif delta.seconds >= 3600:
        rel = f"in {delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
    else:
        rel = f"in {delta.seconds // 60}m"
    return f"  next firing: {dt:%a %b %d %H:%M}  ({rel})"


def cron_to_calendar_interval(parsed: dict) -> str:
    """Render the dict portion of StartCalendarInterval. Only fields with values
    are emitted — omitted fields mean 'every'."""
    fields = []
    label_map = {"minute": "Minute", "hour": "Hour", "day": "Day",
                 "month": "Month", "weekday": "Weekday"}
    for k, label in label_map.items():
        v = parsed.get(k)
        if v is not None:
            fields.append(f"    <key>{label}</key>\n    <integer>{v}</integer>")
    return "\n".join(fields)


def _launchd_label(agent_dir: Path, task_id: str) -> str:
    return f"commando.{agent_dir.name}.{task_id}"


def _plist_path(agent_dir: Path, task_id: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{_launchd_label(agent_dir, task_id)}.plist"


def _render_plist(agent_dir: Path, task_id: str, calendar_interval: str,
                  repo_dir: Path) -> str:
    log_dir = agent_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return PLIST_TEMPLATE.format(
        label=_launchd_label(agent_dir, task_id),
        python=sys.executable,
        task_id=task_id,
        agent_dir=str(agent_dir),
        repo_dir=str(repo_dir),
        path_env=os.environ.get("PATH", ""),
        calendar_interval=calendar_interval,
        log_dir=str(log_dir),
    )


def _launchd_install_task(agent_dir: Path, task: dict, repo_dir: Path, dry: bool) -> bool:
    task_id = task.get("id")
    cron = (task.get("trigger") or {}).get("cron")
    parsed = parse_simple_cron(cron) if cron else None
    if parsed is None:
        click.secho(f"    ! skipped {task_id}: cron '{cron}' uses ranges/lists/steps "
                    f"(v0.2 supports simple single-value expressions only)", fg="yellow")
        return False

    calendar_interval = cron_to_calendar_interval(parsed)
    plist_text = _render_plist(agent_dir, task_id, calendar_interval, repo_dir)
    plist_path = _plist_path(agent_dir, task_id)

    if dry:
        click.echo()
        click.secho(f"    [DRY] would write: {plist_path}", fg="bright_black")
        click.secho(f"    [DRY] would run:   launchctl bootstrap gui/$(id -u) {plist_path}", fg="bright_black")
        return True

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_text, encoding="utf-8")

    # First unload if already loaded (idempotent install)
    subprocess.run(
        ["launchctl", "bootout", f"gui/{os.getuid()}", str(plist_path)],
        capture_output=True,
    )
    r = subprocess.run(
        ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist_path)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        click.secho(f"    ! launchctl bootstrap failed for {task_id}: {r.stderr.strip()[:200]}", fg="yellow")
        return False
    click.secho(f"    ✓ installed {_launchd_label(agent_dir, task_id)}", fg="green")
    click.secho(f"    {_format_next_firing(next_firing(parsed))}", fg="bright_black")
    return True


def _launchd_uninstall_task(agent_dir: Path, task_id: str, dry: bool) -> None:
    plist_path = _plist_path(agent_dir, task_id)
    if not plist_path.exists():
        return

    if dry:
        click.echo()
        click.secho(f"    [DRY] would run:   launchctl bootout gui/$(id -u) {plist_path}", fg="bright_black")
        click.secho(f"    [DRY] would remove: {plist_path}", fg="bright_black")
        return

    subprocess.run(
        ["launchctl", "bootout", f"gui/{os.getuid()}", str(plist_path)],
        capture_output=True,
    )
    plist_path.unlink()
    click.secho(f"    ✓ removed {_launchd_label(agent_dir, task_id)}", fg="green")


def _launchd_list(agent_dir: Path) -> None:
    prefix = f"commando.{agent_dir.name}."
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    if not plist_dir.exists():
        click.echo("  (no LaunchAgents dir)")
        return
    found = sorted(plist_dir.glob(f"{prefix}*.plist"))
    if not found:
        click.echo(f"  No installed launchd jobs for agent '{agent_dir.name}'.")
        return

    for p in found:
        label = p.stem
        r = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
            capture_output=True, text=True,
        )
        loaded = "✓" if r.returncode == 0 else "✗"
        click.echo(f"  {loaded}  {label}  ({p})")


# ──────────────────────────────────────────────────────────────────────────────
# Schedule loader
# ──────────────────────────────────────────────────────────────────────────────

def _load_schedule(agent_dir: Path) -> dict:
    yml = agent_dir / "schedule.yaml"
    if not yml.exists():
        return {}
    try:
        import yaml  # type: ignore
        return yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    except Exception as e:
        click.secho(f"  ✗ failed to parse {yml}: {e}", fg="red")
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# Public entries (called from cli.py)
# ──────────────────────────────────────────────────────────────────────────────

def install(target: str, apply: bool) -> None:
    agent_dir = Path(target).resolve()
    repo_dir = Path(__file__).resolve().parent.parent

    click.echo()
    click.secho("  commando schedule install", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo(f"  agent dir : {agent_dir}")
    click.echo(f"  platform  : {platform.system()}")
    click.echo(f"  mode      : {'APPLY (writes plists, calls launchctl)' if apply else 'DRY-RUN (use --apply for real)'}")

    if platform.system() != "Darwin":
        click.echo()
        click.secho("  ! Non-macOS platform — see docs/scheduling.md for systemd/Task Scheduler.", fg="yellow")
        click.secho("    (macOS launchd is the only verified backend in v0.2.)", fg="yellow")
        return

    schedule = _load_schedule(agent_dir)
    if not schedule:
        click.secho(f"\n  ✗ no schedule.yaml at {agent_dir}", fg="red")
        sys.exit(2)

    cron_tasks = [
        t for t in (schedule.get("tasks") or [])
        if t.get("enabled", True)
        and (t.get("trigger") or {}).get("type") == "cron"
    ]

    if not cron_tasks:
        click.echo()
        click.secho("  no cron tasks in schedule.yaml — nothing to install.", fg="yellow")
        click.echo("  (manual-trigger tasks don't need launchd; trigger them with `commando run --task X`)")
        return

    click.echo()
    click.echo(f"  Found {len(cron_tasks)} cron task(s):")
    installed = 0
    for task in cron_tasks:
        ok = _launchd_install_task(agent_dir, task, repo_dir, dry=not apply)
        if ok:
            installed += 1

    click.echo()
    if apply:
        click.secho(f"  ✓ installed {installed}/{len(cron_tasks)} task(s).", fg="green")
        click.echo()
        click.echo("  launchd is now driving cron firing. Verify with:")
        click.echo("    commando schedule list")
    click.echo()


def uninstall(target: str, apply: bool) -> None:
    agent_dir = Path(target).resolve()
    click.echo()
    click.secho("  commando schedule uninstall", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()

    if platform.system() != "Darwin":
        click.secho("  ! Non-macOS platform.", fg="yellow")
        return

    prefix = f"commando.{agent_dir.name}."
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    found = sorted(plist_dir.glob(f"{prefix}*.plist")) if plist_dir.exists() else []
    if not found:
        click.echo(f"  Nothing installed for agent '{agent_dir.name}'.")
        return

    click.echo(f"  Found {len(found)} installed plist(s):")
    for p in found:
        task_id = p.stem.replace(prefix, "")
        _launchd_uninstall_task(agent_dir, task_id, dry=not apply)

    click.echo()


def list_jobs(target: str) -> None:
    agent_dir = Path(target).resolve()
    click.echo()
    click.secho(f"  commando schedule list  ({agent_dir.name})", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()

    if platform.system() != "Darwin":
        click.secho("  ! Non-macOS platform.", fg="yellow")
        return

    _launchd_list(agent_dir)
    click.echo()

"""commando go-live — the post-onboarding closeout wizard."""
import os
"""

Stranger journey:
    init/onboard → produces my-agent/
        ↓
    go-live → verify + connect IM + install launchd → ship
        ↓
    dashboard → "it's running"

This is the last mile that turns a Configuration directory into a living agent.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import click

from commando.schedule_install import (
    _load_schedule,
    install as schedule_install,
    list_jobs as schedule_list,
    parse_simple_cron,
    next_firing,
    _format_next_firing,
)


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def _validate(agent_dir: Path) -> Tuple[List[Tuple[str, bool, str]], dict]:
    """Return (checks, info_dict). Each check: (label, ok, hint)."""
    checks = []
    info = {}

    charter = agent_dir / "charter.md"
    ok = charter.exists() and len(charter.read_text(encoding="utf-8", errors="ignore")) > 100
    checks.append(("charter.md", ok, "" if ok else f"missing or near-empty at {charter}"))

    skills_dir = agent_dir / "skills"
    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    active = [p for p in skill_files
              if "status: active" in p.read_text(encoding="utf-8", errors="ignore")]
    info["skill_files"] = skill_files
    info["active_skills"] = active
    draft_count = len(skill_files) - len(active)
    if skill_files and len(active) == 0:
        hint = ("All skills are draft placeholders (have metadata, no prompt body). "
                "Step 4 below will build them, or run `commando build-skills --apply`.")
    elif draft_count > 0:
        hint = f"{draft_count} skill(s) still draft — Step 4 can fill them in."
    else:
        hint = ""
    checks.append((
        f"skills ({len(skill_files)} found, {len(active)} active, {draft_count} draft)",
        len(skill_files) > 0,
        hint if skill_files else "no skills/*/SKILL.md found — Onboarding didn't produce skill stubs",
    ))

    schedule_yml = agent_dir / "schedule.yaml"
    schedule = _load_schedule(agent_dir) if schedule_yml.exists() else {}
    tasks = schedule.get("tasks") or []
    cron_tasks = [t for t in tasks if (t.get("trigger") or {}).get("type") == "cron"]
    manual_tasks = [t for t in tasks if (t.get("trigger") or {}).get("type") == "manual"]
    info["cron_tasks"] = cron_tasks
    info["manual_tasks"] = manual_tasks
    checks.append((
        f"schedule.yaml ({len(cron_tasks)} cron, {len(manual_tasks)} manual)",
        schedule_yml.exists() and len(tasks) > 0,
        "" if tasks else "schedule.yaml missing or empty — re-run `commando onboard`",
    ))

    return checks, info


def _check_feishu(agent_dir: Path) -> bool:
    cred = agent_dir / "credentials" / "feishu.yaml"
    return cred.exists() and "notify_chat_id" in cred.read_text(encoding="utf-8", errors="ignore")


def _check_llm_backend() -> Tuple[str, str]:
    """Return (status, detail). status in {'cli', 'sdk', 'none'}."""
    import os
    for binary, label in [("claude", "Claude Code"), ("codex", "Codex"),
                          ("kimi", "Kimi"), ("glm", "GLM"), ("qwen", "Qwen"),
                          ("doubao", "Doubao"), ("minimax", "MiniMax"),
                          ("gemini", "Gemini")]:
        if shutil.which(binary):
            return "cli", f"{label} CLI ({binary})"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "sdk", "ANTHROPIC_API_KEY (headless cron mode)"
    return "none", "no agent CLI in PATH and no API key"


# ──────────────────────────────────────────────────────────────────────────────
# Main wizard
# ──────────────────────────────────────────────────────────────────────────────

def run(target: str, yes: bool = False, skip_im: bool = False,
        skip_schedule: bool = False, skip_build_skills: bool = False) -> None:
    agent_dir = Path(target).resolve()

    click.echo()
    click.secho("  commando go-live", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo(f"  agent dir : {agent_dir}")
    click.echo()

    # ── Step 1 · Validate Configuration ──────────────────────────────────────
    click.secho("  Step 1 · Configuration sanity check", bold=True)
    click.echo()
    checks, info = _validate(agent_dir)
    for label, ok, hint in checks:
        mark = click.style("✓", fg="green") if ok else click.style("✗", fg="red")
        click.echo(f"    {mark}  {label}")
        if hint:
            click.secho(f"        {hint}", fg="yellow")

    if not all(ok for _, ok, _ in checks):
        click.echo()
        click.secho("  ✗ Configuration not ready. Fix the above, then re-run.", fg="red")
        click.echo("    Common fix:  commando onboard --target " + str(agent_dir))
        sys.exit(2)

    # ── Step 2 · LLM backend detection ───────────────────────────────────────
    click.echo()
    click.secho("  Step 2 · LLM backend", bold=True)
    click.echo()
    backend, detail = _check_llm_backend()
    if backend == "none":
        click.secho(f"    ✗ {detail}", fg="red")
        click.echo("      Install an agent CLI (claude / codex / kimi / glm / qwen)")
        click.echo("      OR  export ANTHROPIC_API_KEY=sk-ant-…  for headless cron")
        click.echo()
        click.secho("    Continuing anyway (you can fix this later)…", fg="yellow")
    else:
        mark = click.style("✓", fg="green")
        click.echo(f"    {mark}  using {detail}")

    # ── Step 3 · IM push (optional but recommended) ──────────────────────────
    click.echo()
    click.secho("  Step 3 · IM push", bold=True)
    click.echo()
    has_im = _check_feishu(agent_dir)
    if has_im:
        click.secho("    ✓  Feishu IM already configured", fg="green")
    elif skip_im:
        click.secho("    ⊘  skipped per --skip-im", fg="bright_black")
    else:
        click.echo("    No IM push configured. Without this, your agent runs silently —")
        click.echo("    you won't see Workbench cards in Feishu.")
        click.echo()
        if yes or click.confirm("    Set up Feishu IM now?", default=True):
            from commando.connect_im_feishu import run as _run_im
            _run_im()
            has_im = _check_feishu(agent_dir)
        else:
            click.secho("    skipped (run later: commando connect im-feishu)", fg="bright_black")

    # ── Step 4 · Skill materialization ───────────────────────────────────────
    click.echo()
    click.secho("  Step 4 · Skill materialization", bold=True)
    click.echo()

    skill_files = info["skill_files"]
    active_skills = info["active_skills"]
    draft_count = len(skill_files) - len(active_skills)

    if not skill_files:
        click.echo("    No skills found.")
    elif draft_count == 0:
        click.secho(f"    ✓  all {len(active_skills)} skill(s) already active", fg="green")
    elif skip_build_skills:
        click.secho(f"    ⊘  skipped per --skip-build-skills ({draft_count} draft will stay draft)", fg="bright_black")
    else:
        # Detect whether headless LLM is available (CLI in PATH that won't
        # subprocess-auth-fail, OR an API key set). If neither, default to
        # --print-prompts mode so the user's IDE agent does the work.
        has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY")) or \
                      (agent_dir / "credentials" / "anthropic.yaml").exists()
        headless_likely = has_api_key  # CLI subprocess is too flaky to trust

        click.echo(f"    {draft_count} skill(s) are draft placeholders — they have metadata")
        click.echo("    but no prompt body, so they cannot run at runtime yet.")
        click.echo()
        if headless_likely:
            click.echo("    Headless mode: ANTHROPIC_API_KEY found → will call LLM directly")
            click.echo("    once per skill (~30 sec/skill).")
            click.echo()
            if yes or click.confirm("    Build Skill prompt bodies now?", default=True):
                click.echo()
                from commando.build_skills import run as _run_build
                _run_build(str(agent_dir), apply=True)
            else:
                click.secho("    skipped (run later: commando build-skills --apply)", fg="bright_black")
                click.secho(f"    ! tasks will fail at runtime until {draft_count} skill(s) are built.", fg="yellow")
        else:
            click.echo("    No headless LLM auth detected (no ANTHROPIC_API_KEY).")
            click.echo("    Best path: have your IDE agent (Cascade / Cursor / Claude Code)")
            click.echo("    write the bodies in-conversation — no subprocess, no auth issues.")
            click.echo()
            click.echo("    Run this in your terminal:")
            click.secho("      commando build-skills --print-prompts", fg="green")
            click.echo()
            click.echo("    then paste the printed block into your IDE agent.")
            click.echo()
            click.echo("    Alternatives:")
            click.echo("      · export ANTHROPIC_API_KEY=… then re-run go-live")
            click.echo("      · commando build-skills --apply  (will try subprocess + show fix")
            click.echo("        instructions if auth fails)")

    # ── Step 5 · Install schedule into launchd ───────────────────────────────
    click.echo()
    click.secho("  Step 5 · OS scheduler (launchd)", bold=True)
    click.echo()

    cron_tasks = info["cron_tasks"]
    if not cron_tasks:
        click.echo("    No cron tasks in schedule.yaml — nothing to install.")
        click.echo("    (Manual tasks fire via `commando run --task <id>`.)")
    elif skip_schedule:
        click.secho("    ⊘  skipped per --skip-schedule", fg="bright_black")
    else:
        click.echo(f"    {len(cron_tasks)} cron task(s) will be registered with launchd:")
        for t in cron_tasks:
            cron = (t.get("trigger") or {}).get("cron", "?")
            parsed = parse_simple_cron(cron)
            nxt = _format_next_firing(next_firing(parsed)) if parsed else "  (complex cron not supported)"
            click.echo(f"      · {t['id']}  ({cron})")
            click.secho(f"      {nxt}", fg="bright_black")
        click.echo()
        if yes or click.confirm("    Install these into launchd now?", default=True):
            click.echo()
            schedule_install(str(agent_dir), apply=True)
        else:
            click.secho("    skipped (run later: commando schedule install --apply)", fg="bright_black")

    # ── Step 6 · You're live ─────────────────────────────────────────────────
    click.echo()
    click.secho("  ─── You're live ───", fg="green", bold=True)
    click.echo()
    # Re-validate to pick up newly-built skills
    checks2, info2 = _validate(agent_dir)
    click.echo("    What's running now:")
    click.echo(f"      · {len(info2['active_skills'])} active Skill(s)")
    click.echo(f"      · {len(cron_tasks)} cron task(s) on launchd")
    click.echo(f"      · {len(info2['manual_tasks'])} manual task(s) (trigger with `commando run --task X`)")
    if has_im:
        click.echo(f"      · Feishu IM push enabled")
    click.echo()
    click.echo("    Next steps:")
    click.echo("      commando status              # see what's loaded + next firing")
    click.echo("      commando dashboard           # local web UI")
    click.echo("      commando run --task <id>     # trigger a Skill manually")
    click.echo()

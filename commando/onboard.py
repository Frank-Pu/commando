"""commando onboard — launch Onboarding to produce a real Configuration.

Two paths:
  1. CLI agent in PATH (claude / codex / kimi / glm / qwen / doubao / minimax / gemini)
     → launch subprocess + paste prompt
  2. No CLI found, or user passes --print-prompt
     → print a self-contained kickoff prompt for paste-into-IDE
       (Cursor / Windsurf / VS Code Copilot / JetBrains AI / ChatGPT desktop, etc.)
"""

import shutil
import subprocess
import sys
from pathlib import Path

import click

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "skills" / "onboarding" / "SKILL.md"


PROMPT_TEMPLATE = """Load skills/onboarding/SKILL.md and start Onboarding for me.

Mode: {mode}
Output directory: {target}

If a my-agent/ already exists, ask before overwriting."""


IDE_PROMPT_TEMPLATE = """\
You are about to play the Onboarding facilitator role described in
{skill_path}.

Read that file in full FIRST. It defines your persona, the 4-phase flow
(Role Scoping → Discovery → Calibration → Confirmation), and the
Configuration directory you must produce on disk at the end.

Then start Onboarding for me.

Mode: {mode}
Output directory: {target}

If a my-agent/ already exists, ask before overwriting.

When you reach Confirmation, use your file-write tools to actually create
the Configuration directory — charter.md, schedule.yaml, skills/*, etc.
Do not just paste the content into chat.
"""


def _detect_any_agent_cli():
    """Return (binary, label) of the first agent CLI found in PATH, or None."""
    candidates = [
        ("claude", "Claude Code"), ("codex", "Codex"), ("kimi", "Kimi"),
        ("glm", "GLM"), ("qwen", "Qwen"), ("doubao", "Doubao"),
        ("minimax", "MiniMax"), ("gemini", "Gemini"),
    ]
    for binary, label in candidates:
        if shutil.which(binary):
            return binary, label
    return None


def _print_skill_summary() -> None:
    click.echo()
    click.echo("  What Onboarding does:")
    click.echo("    Phase 0 — Role Scoping (5-10 min)")
    click.echo("    Phase 1 — Discovery: 6 questions in 2 batches")
    click.echo("    Phase 2 — Calibration: 7 decisions you ratify")
    click.echo("    Phase 3 — Confirmation: writes ./my-agent/ to disk")
    click.echo()
    click.echo("  Output:")
    click.echo("    charter.md             — agent's constitution (~250 lines)")
    click.echo("    schedule.yaml          — daily cron tasks")
    click.echo("    skills/ × N            — placeholder Skill files (from Registry or draft)")
    click.echo("    .onboarding/*          — decision trace for Re-onboarding")
    click.echo()


def _print_ide_path(target_path: Path, mode: str) -> None:
    """Print a self-contained kickoff prompt for paste-into-IDE use."""
    prompt = IDE_PROMPT_TEMPLATE.format(skill_path=SKILL_PATH, mode=mode, target=target_path)
    click.echo()
    click.secho("  IDE / paste-anywhere mode", fg="cyan", bold=True)
    click.echo()
    click.echo("  Open this repo in your AI tool of choice (Cursor / Windsurf /")
    click.echo("  VS Code Copilot / JetBrains AI / Claude Desktop / ChatGPT desktop…)")
    click.echo("  and paste the following prompt:")
    click.echo()
    click.secho("  ─── Copy from here ─────────────────────────────────────────", fg="bright_black")
    for line in prompt.split("\n"):
        click.secho(f"  {line}", fg="green")
    click.secho("  ─── To here ────────────────────────────────────────────────", fg="bright_black")
    click.echo()
    click.echo(f"  When the agent finishes, your Configuration will be at: {target_path}")
    click.echo()
    click.echo("  Then close the loop:")
    click.echo("    commando go-live    # validate + connect IM + install launchd")
    click.echo()


def run(target: str, mode: str, force: bool, skip_go_live: bool = False,
        print_prompt: bool = False) -> None:
    click.echo()
    click.secho("  commando onboard", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")

    target_path = Path(target).resolve()

    # --print-prompt mode: skip detection, just print and exit
    if print_prompt:
        _print_ide_path(target_path, mode)
        return

    # Step 1 — detect ANY agent CLI
    click.echo()
    click.echo("  Step 1 · Detecting your AI tool")
    found = _detect_any_agent_cli()
    if found is None:
        click.secho("    ✗ no agent CLI in PATH", fg="yellow")
        click.echo()
        click.echo("    No problem — Onboarding works in any IDE / AI tool too.")
        _print_ide_path(target_path, mode)
        sys.exit(0)
    binary, label = found
    claude_path = shutil.which(binary)
    click.secho(f"    ✓ found {label} at {claude_path}", fg="green")

    # Step 2 — target dir check
    click.echo()
    click.echo("  Step 2 · Target directory")
    if target_path.exists() and any(target_path.iterdir()) and not force:
        click.secho(f"    ! {target_path} already exists with content.", fg="yellow")
        click.echo()
        click.echo("    Options:")
        click.echo("      a) pick a different dir:")
        click.echo("           commando onboard --target ./my-other-agent")
        click.echo("      b) re-run Onboarding to refine the existing one (Re-onboarding):")
        click.echo("           commando onboard --target ./my-agent --force")
        click.echo("      c) abort, manually delete, then re-run")
        if not click.confirm(f"    Continue with {target_path}?", default=False):
            click.secho("    aborted.", fg="yellow")
            sys.exit(1)
    else:
        click.secho(f"    ✓ {target_path}", fg="green")

    _print_skill_summary()

    # Step 3 — kickoff
    click.echo()
    click.echo(f"  Step 3 · Starting {label}")
    click.echo()
    click.echo(f"    {label} will open in this directory. When it's ready, paste:")
    click.echo()
    prompt = PROMPT_TEMPLATE.format(mode=mode, target=target_path)
    for line in prompt.split("\n"):
        click.secho(f"      {line}", fg="green")
    click.echo()

    if not click.confirm(f"    Launch `{binary}` now?", default=True):
        click.echo()
        click.echo("    To start manually:")
        click.echo(f"      cd {REPO_ROOT}")
        click.echo(f"      {binary}")
        click.echo("      (paste the prompt above)")
        click.echo()
        click.echo("    Or use it in your IDE instead:")
        click.echo("      commando onboard --print-prompt")
        click.echo()
        sys.exit(0)

    click.echo()
    click.secho(f"  Launching {label}… (Ctrl-D or /exit to quit)", fg="bright_black")
    click.echo()
    try:
        subprocess.run([binary], cwd=str(REPO_ROOT))
    except KeyboardInterrupt:
        pass
    click.echo()
    click.secho(f"  {label} exited.", fg="cyan")
    click.echo()

    # ── Step 4 · auto-chain into go-live ─────────────────────────────────────
    if skip_go_live:
        click.echo(f"  Configuration in: {target_path}")
        click.echo("  Run later:  commando go-live")
        click.echo()
        return

    schedule_yml = target_path / "schedule.yaml"
    charter = target_path / "charter.md"
    if not (schedule_yml.exists() and charter.exists()):
        click.secho("  ! Configuration looks incomplete — skipping go-live.", fg="yellow")
        click.echo(f"    Looked for: {charter} and {schedule_yml}")
        click.echo("    Re-run Onboarding inside Claude Code, or run `commando go-live` manually.")
        click.echo()
        return

    click.echo("  Step 4 · Closeout — IM connect + launchd install")
    click.echo()
    if not click.confirm("    Run `commando go-live` now to finish setup?", default=True):
        click.echo()
        click.echo("    When ready:  commando go-live")
        click.echo()
        return

    from commando.go_live import run as _run_go_live
    _run_go_live(str(target_path))

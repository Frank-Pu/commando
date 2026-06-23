"""commando onboard — launch Onboarding to produce a real Configuration.

v0.1: detect `claude` CLI; either launch it (with a copy-pastable prompt) or
provide install instructions. Onboarding itself happens INSIDE Claude Code,
driven by skills/onboarding/SKILL.md.

v0.2 will pass the SKILL.md to claude with --skill flag (if/when that lands)
or auto-paste the kickoff prompt via stdin.
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


def run(target: str, mode: str, force: bool) -> None:
    click.echo()
    click.secho("  commando onboard", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")

    target_path = Path(target).resolve()

    # Step 1 — detect claude CLI
    click.echo()
    click.echo("  Step 1 · Detecting Claude Code")
    claude_path = shutil.which("claude")
    if claude_path is None:
        click.secho("    ✗ `claude` CLI not in PATH", fg="red")
        click.echo()
        click.echo("    Install Claude Code:")
        click.secho("      https://docs.claude.com/en/docs/claude-code/getting-started", fg="blue")
        click.echo()
        click.echo("    After install, run `claude` to authenticate, then re-run:")
        click.echo("      commando onboard")
        click.echo()
        click.echo("    Alternative (no Claude Code):")
        click.echo("      commando init   # copy a sample Configuration to play with")
        click.echo()
        sys.exit(2)
    click.secho(f"    ✓ found at {claude_path}", fg="green")

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
    click.echo("  Step 3 · Starting Claude Code")
    click.echo()
    click.echo("    Claude Code will open in this directory. When it's ready, paste:")
    click.echo()
    prompt = PROMPT_TEMPLATE.format(mode=mode, target=target_path)
    for line in prompt.split("\n"):
        click.secho(f"      {line}", fg="green")
    click.echo()

    if not click.confirm("    Launch `claude` now?", default=True):
        click.echo()
        click.echo("    To start manually:")
        click.echo(f"      cd {REPO_ROOT}")
        click.echo("      claude")
        click.echo("      (paste the prompt above)")
        click.echo()
        sys.exit(0)

    click.echo()
    click.secho("  Launching Claude Code… (Ctrl-D or /exit to quit)", fg="bright_black")
    click.echo()
    try:
        subprocess.run(["claude"], cwd=str(REPO_ROOT))
    except KeyboardInterrupt:
        pass
    click.echo()
    click.echo(f"  When Claude Code finishes, check {target_path} for the new Configuration.")
    click.echo("  Then:  commando dashboard")
    click.echo()

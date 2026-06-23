"""commando init — bootstrap a Configuration directory from a packaged example.

This is the "quick demo" path. Real users should `commando onboard` instead
to produce a Configuration that fits THEIR product / role.
"""

import shutil
import sys
from pathlib import Path

import click

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"


AVAILABLE_TEMPLATES = {
    "lemingle-growth-partner": {
        "source": "examples/lemingle-growth-partner",
        "label": "阿土 · LeMingle 增长合伙人（atu 半年实跑沉淀，full Configuration）",
    },
}


def _list_templates() -> None:
    click.echo("  Available templates:")
    for slug, meta in AVAILABLE_TEMPLATES.items():
        click.echo(f"    {slug}")
        click.secho(f"      {meta['label']}", fg="bright_black")


def _augment_sample(target: Path) -> None:
    """The example dir has charter + schedule. The sample needs runtime dirs +
    event-routing.yaml + a 'this is a sample' banner."""

    # event-routing.yaml — copy from the live my-agent/ if present, else write a minimal one
    routing_target = target / "event-routing.yaml"
    if not routing_target.exists():
        live_routing = REPO_ROOT / "my-agent" / "event-routing.yaml"
        if live_routing.exists():
            shutil.copy2(live_routing, routing_target)
        else:
            routing_target.write_text(
                "# event-routing.yaml v0.1 — empty starter\n"
                "# See commando/docs/event-bus.md for the rules schema.\n"
                "version: 0.1\n"
                "rules: []\n"
                "destinations: {}\n",
                encoding="utf-8",
            )

    # empty runtime dirs (so dashboard / runtime don't trip)
    for sub in ("backends", "workbench", "memory/working", "memory/episodic", "memory/semantic"):
        (target / sub).mkdir(parents=True, exist_ok=True)

    # banner in README
    readme = target / "README.md"
    banner = (
        "> ⚠️ **This is a sample Configuration copied via `commando init`.**\n"
        "> It serves the LeMingle product (an indie language-learning Chrome extension).\n"
        "> To produce a Configuration that fits YOUR product / role:\n"
        ">\n"
        ">     commando onboard\n"
        ">\n"
        "> That starts a 25-90 min conversation with Claude Code and writes a real\n"
        "> Configuration tailored to your situation. See docs/example-onboarding-transcript.md.\n\n"
    )
    if readme.exists():
        existing = readme.read_text(encoding="utf-8")
        if "This is a sample Configuration" not in existing:
            readme.write_text(banner + existing, encoding="utf-8")
    else:
        readme.write_text(banner, encoding="utf-8")


def run(target_dir: str, template: str, force: bool) -> None:
    target = Path(target_dir).resolve()

    if template == "list" or template not in AVAILABLE_TEMPLATES:
        click.echo()
        if template not in AVAILABLE_TEMPLATES and template != "list":
            click.secho(f"  ✗ unknown template: {template}", fg="red")
            click.echo()
        _list_templates()
        click.echo()
        click.echo("  Usage:  commando init [DIR] --template <slug>")
        sys.exit(0 if template == "list" else 2)

    source = REPO_ROOT / AVAILABLE_TEMPLATES[template]["source"]
    if not source.exists():
        click.secho(f"  ✗ template source missing: {source}", fg="red")
        sys.exit(2)

    click.echo()
    click.secho("  commando init", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo(f"  template: {template}")
    click.echo(f"  target  : {target}")
    click.echo()

    if target.exists() and any(target.iterdir()):
        if not force:
            click.secho(f"  ! {target} already exists and is non-empty.", fg="yellow")
            if not click.confirm("    Overwrite (merge files)?", default=False):
                click.secho("    aborted.", fg="yellow")
                sys.exit(1)
        click.echo()

    target.mkdir(parents=True, exist_ok=True)

    # copy each file from the template (don't replace target if exists w/o confirm)
    copied = 0
    for src_path in source.rglob("*"):
        if src_path.is_dir():
            continue
        rel = src_path.relative_to(source)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst)
        copied += 1

    click.secho(f"  ✓ copied {copied} files from {AVAILABLE_TEMPLATES[template]['source']}", fg="green")

    _augment_sample(target)
    click.secho(f"  ✓ added event-routing.yaml + runtime dirs + sample banner", fg="green")

    click.echo()
    click.echo("  What you have now:")
    click.echo(f"    {target}/charter.md           — agent constitution (LeMingle's)")
    click.echo(f"    {target}/schedule.yaml        — daily cron task list")
    click.echo(f"    {target}/event-routing.yaml   — IM push rules")
    click.echo(f"    {target}/skills/              — (empty in this template — onboarding writes them)")
    click.echo()
    click.echo("  Next steps:")
    click.echo("    commando dashboard               · see the agent")
    click.echo("    commando connect im-feishu       · wire up Feishu IM (3 min)")
    click.echo("    commando route --demo im --apply · send a real card")
    click.echo()
    click.secho("  When ready to make it YOUR agent (not LeMingle):", fg="cyan")
    click.echo("    commando onboard                 · 25-90 min conversation, real Configuration")
    click.echo()

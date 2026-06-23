"""commando CLI — unified entrypoint for onboard / connect / materialize / route / dashboard / run."""

import os
import runpy
import subprocess
import sys
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DASHBOARD = ROOT / "dashboard"
SKILLS = ROOT / "skills"


def _run_tool(name: str, args: list) -> None:
    """Invoke tools/<name>.py as if run directly, preserving its argparse."""
    script = TOOLS / f"{name}.py"
    if not script.exists():
        click.echo(f"error: {script} not found", err=True)
        sys.exit(2)
    sys.argv = [str(script)] + list(args)
    runpy.run_path(str(script), run_name="__main__")


def _print_panel(title: str, lines: list, color: str = "cyan") -> None:
    click.echo()
    click.secho(f"  {title}", fg=color, bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    for line in lines:
        click.echo(f"  {line}")
    click.echo()


from commando import __version__


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="commando — Runtime is commodity. Configuration is the moat.",
)
@click.version_option(version=__version__, prog_name="commando")
def cli():
    pass


# ──────────────────────────────────────────────────────────────────────────────
# commando init — bootstrap a Configuration from a packaged sample
# ──────────────────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("dir", default="./my-agent", required=False)
@click.option("--template", default="lemingle-growth-partner",
              help="Sample template slug (or 'list' to see available).")
@click.option("--force", is_flag=True, help="Overwrite existing files without asking.")
def init(dir, template, force):
    """Bootstrap a Configuration directory from a packaged sample."""
    from commando.init import run as _run

    _run(dir, template, force)


# ──────────────────────────────────────────────────────────────────────────────
# commando onboard — launch Onboarding (Claude Code)
# ──────────────────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--target", default="./my-agent", help="Output Configuration directory.")
@click.option("--mode", type=click.Choice(["express", "full"]), default="express",
              help="Express ≈ 25 min, full ≈ 60-120 min.")
@click.option("--force", is_flag=True, help="Skip the 'target exists' confirmation.")
def onboard(target, mode, force):
    """Start Onboarding — talk to Claude Code, produce a real Configuration."""
    from commando.onboard import run as _run

    _run(target, mode, force)


# ──────────────────────────────────────────────────────────────────────────────
# commando connect — guided setup for backends / IM connectors
# ──────────────────────────────────────────────────────────────────────────────
@cli.group(help="Connect a backend / IM / data source.")
def connect():
    pass


@connect.command("im-feishu", help="Guided setup for Feishu IM push.")
def connect_im_feishu():
    from commando.connect_im_feishu import run as _run_im_feishu

    _run_im_feishu()


@connect.command("feishu", help="Stub — full backend connection (bitable + wiki) coming in v0.2.")
def connect_feishu():
    _print_panel(
        "Coming in v0.2 — Feishu backend driver auto-generation",
        [
            "For now, atu provides a working reference implementation:",
            "  https://github.com/Frank-Pu/atu/tree/main/connectors/feishu",
            "",
            "v0.2 will guide your local agent (Claude Code) to generate",
            "a similar driver in ./my-agent/backends/feishu/ from atu's pattern.",
        ],
    )


@connect.command("notion", help="Stub — Notion backend (v0.3+).")
def connect_notion():
    _print_panel("Coming in v0.3+ — Notion backend driver", ["Vote for it: github.com/Frank-Pu/commando/issues"])


# ──────────────────────────────────────────────────────────────────────────────
# commando materialize — pass through to tools/materialize.py
# ──────────────────────────────────────────────────────────────────────────────
@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True, "help_option_names": []},
    help="Render Configuration to a backend (dry-run by default; pass --apply for real).",
)
@click.pass_context
def materialize(ctx):
    _run_tool("materialize", ctx.args)


# ──────────────────────────────────────────────────────────────────────────────
# commando route — pass through to tools/route.py
# ──────────────────────────────────────────────────────────────────────────────
@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True, "help_option_names": []},
    help="Route Episodic events to IM (dry-run by default; pass --apply for real).",
)
@click.pass_context
def route(ctx):
    _run_tool("route", ctx.args)


# ──────────────────────────────────────────────────────────────────────────────
# commando dashboard — launch the local web dashboard
# ──────────────────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--port", default=7878, help="Port to bind (default 7878).")
@click.option("--no-browser", is_flag=True, help="Do not auto-open the browser.")
@click.option("--agent-dir", default=None, help="Configuration directory (default: ./my-agent/).")
def dashboard(port, no_browser, agent_dir):
    """Launch the local commando dashboard."""
    server = DASHBOARD / "server.py"
    if not server.exists():
        click.echo(f"error: {server} not found", err=True)
        sys.exit(2)
    cmd = [sys.executable, str(server), "--port", str(port)]
    if no_browser:
        cmd.append("--no-browser")
    if agent_dir:
        cmd += ["--agent-dir", agent_dir]
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        sys.stderr.write("\nshutting down dashboard\n")


# ──────────────────────────────────────────────────────────────────────────────
# commando run — one-shot Skill execution (v0.2 minimum Runtime)
# ──────────────────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--task", "task_id", required=True, help="Task id from schedule.yaml.")
@click.option("--agent-dir", "target", default="./my-agent")
@click.option("--apply", is_flag=True, help="Actually call Anthropic API (default: dry-run).")
@click.option("--inputs", default=None, help="Override user message sent to the Skill.")
def run(task_id, target, apply, inputs):
    """Execute a task from schedule.yaml (one-shot, manual trigger)."""
    from commando.run import run as _run

    _run(target, task_id, apply, inputs)


# ──────────────────────────────────────────────────────────────────────────────
# commando install — pull a Skill from the Registry (stub for v0.1)
# ──────────────────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("skill_id", required=False)
def install(skill_id):
    """Install a Skill from the registry into ./my-agent/skills/."""
    if not skill_id:
        click.echo("Usage: commando install @author/skill-name")
        click.echo("Example: commando install @frank-pu/xhs-bilingual-bridge")
        return
    _print_panel(
        "Coming in v0.2 — Skill installer",
        [
            f"Requested: {skill_id}",
            "",
            "Registry: skills.json (root of this repo)",
            "Resolution rule: @author/name → source_url field → git clone subtree",
            "",
            "For now, manually copy from atu:",
            "  https://github.com/Frank-Pu/atu/tree/main/configuration/skills",
        ],
        color="yellow",
    )


def main():
    cli()


if __name__ == "__main__":
    main()

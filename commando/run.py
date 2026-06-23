"""commando run — execute a single task one-shot.

v0.2 scope: read schedule.yaml, find the task by id, fan out to its Skills.
For simplicity in v0.2: if a task has multiple skills, execute them sequentially.
"""

import sys
from pathlib import Path

import click

from commando.runtime.skill_runner import execute_skill


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


def _find_task(schedule: dict, task_id: str) -> dict:
    for task in (schedule.get("tasks") or []):
        if task.get("id") == task_id:
            return task
    return {}


def run(target: str, task_id: str, apply: bool, inputs: str) -> None:
    agent_dir = Path(target).resolve()

    click.echo()
    click.secho("  commando run", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo(f"  agent dir : {agent_dir}")
    click.echo(f"  task id   : {task_id}")
    click.echo(f"  mode      : {'APPLY (real LLM call)' if apply else 'DRY-RUN (use --apply for real)'}")

    if not agent_dir.exists():
        click.secho(f"\n  ✗ agent dir not found: {agent_dir}", fg="red")
        click.echo("    Run: commando init   to bootstrap a sample.")
        sys.exit(2)

    schedule = _load_schedule(agent_dir)
    task = _find_task(schedule, task_id)
    if not task:
        click.echo()
        click.secho(f"  ✗ task '{task_id}' not found in {agent_dir}/schedule.yaml", fg="red")
        click.echo("\n    Available task ids:")
        for t in (schedule.get("tasks") or []):
            enabled = "✓" if t.get("enabled", True) else "✗"
            trigger = (t.get("trigger") or {}).get("type", "?")
            click.echo(f"      [{enabled}] {t.get('id'):24s} trigger={trigger:8s} skills={t.get('skills')}")
        sys.exit(2)

    skills = task.get("skills") or []
    if not skills:
        click.secho(f"\n  ! task '{task_id}' has no skills array", fg="yellow")
        sys.exit(0)

    click.echo()
    click.echo(f"  task name : {task.get('name', task_id)}")
    click.echo(f"  skills    : {skills}")
    click.echo()

    for skill_name in skills:
        click.echo()
        click.secho(f"  ──── skill: {skill_name} ────", fg="cyan")
        try:
            result = execute_skill(
                agent_dir=agent_dir,
                skill_name=skill_name,
                task_id=task_id,
                inputs=inputs,
                dry=not apply,
            )
        except FileNotFoundError as e:
            click.secho(f"   ✗ {e}", fg="red")
            continue
        except Exception as e:
            click.secho(f"   ✗ unexpected error: {e}", fg="red")
            continue

        if result.get("status") in ("failed",):
            click.secho("\n  Stopping fan-out due to failure.", fg="yellow")
            sys.exit(1)

    click.echo()
    if apply:
        click.echo("  ✓ done. dashboard Activity tab should show the new events.")
        click.echo("    commando dashboard")
    click.echo()

#!/usr/bin/env python3
"""
commando materialize — render a Configuration to a backend platform.

v0.1 supports `--backend feishu` in **dry-run mode by default**: it reads
my-agent/{charter.md, schedule.yaml, connectors.yaml, skills/} and emits a
plan + the concrete lark-cli commands that *would* be executed. Pass
`--apply` to actually invoke lark-cli (requires `commando connect feishu`
to have set up credentials).

Examples
    python tools/materialize.py --agent-dir ./my-agent
    python tools/materialize.py --agent-dir ./my-agent --backend feishu
    python tools/materialize.py --agent-dir ./my-agent --backend feishu --apply

Design — see docs/feishu-backend.md.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        sys.stderr.write("error: pyyaml required (pip install pyyaml)\n")
        sys.exit(2)
    except FileNotFoundError:
        return {}
    except Exception as e:
        sys.stderr.write(f"error: failed to parse {path}: {e}\n")
        sys.exit(2)


def load_agent_name(agent_dir: Path) -> str:
    charter = agent_dir / "charter.md"
    if not charter.exists():
        return "agent"
    for line in charter.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("# Charter:"):
            rest = line.replace("# Charter:", "").strip()
            return rest.split("·")[0].strip() if "·" in rest else rest
    return "agent"


def load_skills(agent_dir: Path) -> list:
    skills_dir = agent_dir / "skills"
    if not skills_dir.exists():
        return []
    out = []
    for sub in sorted(skills_dir.iterdir()):
        if sub.is_dir() and (sub / "SKILL.md").exists():
            out.append(sub.name)
    return out


class Action:
    def __init__(self, kind: str, label: str, cmd: Optional[list] = None, note: str = ""):
        self.kind = kind
        self.label = label
        self.cmd = cmd or []
        self.note = note


def plan(agent_dir: Path, backend: str, profile: Optional[str]) -> list:
    if backend != "feishu":
        sys.stderr.write(f"error: backend '{backend}' not supported in v0.1 (only 'feishu')\n")
        sys.exit(2)

    name = load_agent_name(agent_dir)
    schedule = load_yaml(agent_dir / "schedule.yaml")
    connectors = load_yaml(agent_dir / "connectors.yaml")
    skills = load_skills(agent_dir)

    feishu_cfg = (connectors.get("backend") or {}).get("feishu") or {}
    workspace = feishu_cfg.get("workspaces") or {}
    wiki_space = workspace.get("wiki_space_id") or "<WIKI_SPACE_ID>"
    bitable_token = workspace.get("bitable_app_token") or "<NEW_BITABLE>"
    profile_flag = ["--profile", profile] if profile else []

    actions = []

    actions.append(Action(
        "wiki", f"upsert Wiki node 「Charter — {name}」",
        ["lark-cli", "wiki", "+upsert-node",
         "--space-id", wiki_space, "--title", f"Charter — {name}",
         "--from-file", str(agent_dir / "charter.md")] + profile_flag,
        "Charter is single-source-of-truth in local file; Wiki is a read-only mirror.",
    ))

    actions.append(Action(
        "wiki", "upsert Wiki sub-node 「📚 Skills」 (index)",
        ["lark-cli", "wiki", "+upsert-node",
         "--space-id", wiki_space, "--title", "Skills",
         "--parent-title", f"Charter — {name}"] + profile_flag,
        "Index page; each skill is a child node below.",
    ))

    for skill in skills:
        actions.append(Action(
            "wiki", f"upsert Wiki node 「Skill · {skill}」",
            ["lark-cli", "wiki", "+upsert-node",
             "--space-id", wiki_space, "--title", f"Skill · {skill}",
             "--parent-title", "Skills",
             "--from-file", str(agent_dir / "skills" / skill / "SKILL.md")] + profile_flag,
        ))

    actions.append(Action(
        "bitable", "create Bitable app 「Workbench」 (with 4 views)",
        ["lark-cli", "bitable", "+create-app",
         "--name", f"{name} · Workbench",
         "--workspace", wiki_space,
         "--schema-file", "tools/feishu-bitable-workbench-schema.json"] + profile_flag,
        "Schema has both template + instance row types via `type` field. Views: calendar / kanban / gantt / table.",
    ))

    tasks = schedule.get("tasks", []) if isinstance(schedule, dict) else []
    for task in tasks:
        tid = task.get("id", "?")
        actions.append(Action(
            "bitable-row", f"insert template row 「{tid}」",
            ["lark-cli", "bitable", "+insert-record",
             "--app-token", bitable_token, "--table", "Workbench",
             "--fields", _serialize_task_row(task)] + profile_flag,
        ))

    actions.append(Action(
        "im", "register IM bot listener for task state changes",
        ["lark-cli", "events", "+subscribe",
         "--types", "bitable.record_changed",
         "--app-token", bitable_token,
         "--callback", "commando-runtime"] + profile_flag,
        "When you flip a row in Feishu, runtime hears about it and syncs back.",
    ))

    return actions


def _serialize_task_row(task: dict) -> str:
    trigger = task.get("trigger", {}) or {}
    return ",".join([
        f"type=template",
        f"task_id={task.get('id', '')}",
        f"name={task.get('name', '')}",
        f"trigger_type={trigger.get('type', '')}",
        f"cron={trigger.get('cron', '')}",
        f"skills={'|'.join(task.get('skills') or [])}",
        f"requires_human_approval={'true' if task.get('requires_human_approval') else 'false'}",
        f"enabled={'true' if task.get('enabled', True) else 'false'}",
    ])


def render_plan(actions: list, color: bool = True) -> None:
    def c(s, code):
        return f"\033[{code}m{s}\033[0m" if color and sys.stdout.isatty() else s

    print()
    print(c("commando materialize · plan", "1;36"))
    print(c("─" * 60, "2"))
    print(f"  {len(actions)} action(s) planned")
    print()
    for i, act in enumerate(actions, 1):
        kind_color = {"wiki": "36", "bitable": "33", "bitable-row": "33", "im": "35"}.get(act.kind, "0")
        print(f"  {c(f'{i:>2}.', '1')} [{c(act.kind, kind_color)}] {act.label}")
        if act.note:
            print(f"       {c('— ' + act.note, '2')}")
        print(f"       {c('$ ' + ' '.join(act.cmd), '2')}")
        print()


def apply_plan(actions: list) -> int:
    if shutil.which("lark-cli") is None:
        sys.stderr.write("error: lark-cli not found in PATH. install + run `commando connect feishu` first.\n")
        return 2
    fails = 0
    for i, act in enumerate(actions, 1):
        print(f"[{i}/{len(actions)}] {act.label} …")
        try:
            r = subprocess.run(act.cmd, capture_output=True, text=True)
            if r.returncode != 0:
                fails += 1
                sys.stderr.write(f"  failed (rc={r.returncode}): {r.stderr.strip()[:200]}\n")
        except Exception as e:
            fails += 1
            sys.stderr.write(f"  exception: {e}\n")
    return 0 if fails == 0 else 1


def main():
    p = argparse.ArgumentParser(prog="commando-materialize")
    p.add_argument("--agent-dir", default="./my-agent",
                   help="Path to Configuration directory (default: ./my-agent/)")
    p.add_argument("--backend", default="feishu", choices=["feishu"],
                   help="Backend to materialize to")
    p.add_argument("--profile", default=None,
                   help="lark-cli --profile to pass (e.g. cli_a9660c… for user app)")
    p.add_argument("--apply", action="store_true",
                   help="Actually invoke lark-cli (default: dry-run)")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    agent_dir = Path(args.agent_dir).resolve()
    if not agent_dir.exists():
        sys.stderr.write(f"error: agent dir {agent_dir} not found\n")
        sys.exit(2)

    actions = plan(agent_dir, args.backend, args.profile)
    render_plan(actions, color=not args.no_color)

    if args.apply:
        print("──── applying ────")
        sys.exit(apply_plan(actions))
    else:
        print("(dry-run · no commands executed · pass --apply to invoke lark-cli)")


if __name__ == "__main__":
    main()

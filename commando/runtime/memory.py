"""Episodic Memory write — append events to memory/episodic/<date>.jsonl.

dashboard reads these via /api/data → activity tab projects them.
Same format as the mock activity events.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional


def write_episodic(agent_dir: Path, event: dict) -> Path:
    """Append a single event to today's episodic jsonl. Returns the path."""
    today = date.today().isoformat()
    epdir = agent_dir / "memory" / "episodic"
    epdir.mkdir(parents=True, exist_ok=True)
    path = epdir / f"{today}.jsonl"
    # ensure ts exists
    event = dict(event)
    event.setdefault("ts", datetime.now().astimezone().isoformat())
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def make_event(
    *,
    level: str,
    agent_id: str,
    skill: str,
    task_id: str,
    message: str,
    duration_ms: Optional[int] = None,
    artifact_uri: Optional[str] = None,
    workbench_uri: Optional[str] = None,
) -> dict:
    """Build a level/skill/task event matching the schema in docs/event-bus.md."""
    ev: dict = {
        "event_id": f"{agent_id}-{datetime.now().isoformat()}",
        "level": level,
        "agent_id": agent_id,
        "skill": skill,
        "task_id": task_id,
        "message": message,
    }
    if duration_ms is not None:
        ev["duration_ms"] = duration_ms
    if artifact_uri:
        ev["artifact_uri"] = artifact_uri
    if workbench_uri:
        ev["workbench_uri"] = workbench_uri
    return ev

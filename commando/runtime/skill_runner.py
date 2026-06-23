"""skill_runner — load a Skill, inject Charter, call LLM, write event."""

import re
import time
from pathlib import Path
from typing import Optional, Tuple

from commando.runtime.llm import call_skill
from commando.runtime.memory import make_event, write_episodic


def load_skill(agent_dir: Path, skill_name: str) -> Tuple[dict, str]:
    """Load skills/<name>/SKILL.md. Returns (frontmatter, body)."""
    skill_md = agent_dir / "skills" / skill_name / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"Skill not found: {skill_md}")

    text = skill_md.read_text(encoding="utf-8")
    return parse_frontmatter(text)


def parse_frontmatter(text: str) -> Tuple[dict, str]:
    """Parse `---\nyaml\n---\nbody` markdown. Returns (frontmatter dict, body str)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")

    try:
        import yaml  # type: ignore
        fm = yaml.safe_load(block) or {}
        if not isinstance(fm, dict):
            fm = {}
    except Exception:
        fm = {}
        for line in block.splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def load_charter_context(agent_dir: Path) -> str:
    """Read charter.md. Per docs/charter.md spec, first 5 sections auto-inject
    on every Skill call. v0.2 minimal: return the full document."""
    charter = agent_dir / "charter.md"
    if not charter.exists():
        return ""
    return charter.read_text(encoding="utf-8")


def execute_skill(
    *,
    agent_dir: Path,
    skill_name: str,
    task_id: str,
    inputs: Optional[str] = None,
    dry: bool = True,
) -> dict:
    """Execute one Skill. Writes events to episodic before/after."""
    agent_id = agent_dir.name

    # Load Skill + Charter
    fm, body = load_skill(agent_dir, skill_name)
    charter = load_charter_context(agent_dir)

    # Build system prompt: charter + skill body
    system_prompt = charter
    if charter:
        system_prompt += "\n\n---\n\n# Active Skill: " + skill_name + "\n\n"
    system_prompt += body

    user_message = inputs or "Begin executing this Skill now."
    model = fm.get("model") or "claude-opus-4-7"
    status = fm.get("status", "active")

    # Refuse to execute draft / imported-placeholder skills
    if status in ("draft", "imported-placeholder"):
        print(f"   ! skill '{skill_name}' has status='{status}' — refusing to execute")
        print(f"     Update skills/{skill_name}/SKILL.md frontmatter to status='active' to run.")
        return {"status": "skipped_due_to_status", "skill_status": status}

    # Write "trigger" event
    if not dry:
        trig = make_event(
            level="trigger", agent_id=agent_id, skill=skill_name,
            task_id=task_id, message=f"manual · commando run --task {task_id}",
        )
        write_episodic(agent_dir, trig)

    # Dry-run preview
    if dry:
        print(f"   · skill        : {skill_name}")
        print(f"   · model        : {model}")
        print(f"   · status       : {status}")
        print(f"   · system prompt: {len(system_prompt)} chars ({len(charter)} from charter, {len(body)} from skill body)")
        print(f"   · user message : {user_message}")
        print(f"   · (pass --apply to actually call Anthropic API)")
        return {"status": "dry_run_only", "system_prompt_chars": len(system_prompt)}

    # Real LLM call
    print(f"   · calling {model}… ({len(system_prompt)} chars system)")
    t0 = time.time()
    try:
        result = call_skill(
            agent_dir=agent_dir,
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
        )
    except RuntimeError as e:
        # Write failure event
        fail_ev = make_event(
            level="done", agent_id=agent_id, skill=skill_name,
            task_id=task_id, message=f"FAILED: {str(e)[:200]}",
        )
        write_episodic(agent_dir, fail_ev)
        print(f"   ✗ {e}")
        return {"status": "failed", "error": str(e)}

    duration_ms = int((time.time() - t0) * 1000)
    response_text = result["response_text"]

    print()
    print(f"   ✓ {result['model']} · {result['input_tokens']} in / {result['output_tokens']} out · {duration_ms} ms")
    print(f"   ──────────────")
    for line in response_text.strip().split("\n"):
        print(f"   {line}")
    print(f"   ──────────────")

    # Write done event
    done_ev = make_event(
        level="done", agent_id=agent_id, skill=skill_name,
        task_id=task_id, message=response_text.strip()[:200],
        duration_ms=duration_ms,
    )
    ep_path = write_episodic(agent_dir, done_ev)
    print()
    print(f"   wrote event to {ep_path.relative_to(agent_dir.parent) if ep_path.is_relative_to(agent_dir.parent) else ep_path}")

    return {
        "status": "ok",
        "response_text": response_text,
        "duration_ms": duration_ms,
        "tokens": result["input_tokens"] + result["output_tokens"],
    }

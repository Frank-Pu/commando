"""commando install — pull a Skill from anywhere into my-agent/skills/.

Four source types, one unified flow:
    @author/name              → Registry lookup in skills.json
    https://…/SKILL.md        → URL fetch (auto-converts github blob URLs)
    git+https://repo[#path]   → git clone subpath
    ./local/path or file://   → local copy
    --paste / interactive     → stdin / editor

After install:
    · drop into my-agent/skills/<name>/SKILL.md (with `source:` provenance)
    · offer: rebuild prompt body against THIS agent's Charter (build_skills)
    · offer: add to schedule.yaml with a cron suggested from tags
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import click


REPO_ROOT = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────────────────
# Source resolution
# ──────────────────────────────────────────────────────────────────────────────

def _detect_source_type(source: str) -> str:
    if source.startswith("@"):
        return "registry"
    if source.startswith("git+"):
        return "git"
    if source.startswith(("http://", "https://")):
        return "url"
    if source.startswith("file://") or source.startswith("/") or source.startswith("./"):
        return "local"
    return "unknown"


def _normalize_github_url(url: str) -> str:
    """github.com/.../blob/main/x.md → raw.githubusercontent.com/.../main/x.md"""
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url


def _fetch_url(url: str) -> str:
    url = _normalize_github_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": "commando-install/0.1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")


def _fetch_registry(handle: str) -> Tuple[str, dict]:
    """Returns (content, registry_entry). Handle like '@frank-pu/skill-name'."""
    skills_json = REPO_ROOT / "skills.json"
    if not skills_json.exists():
        raise RuntimeError("skills.json not found in repo root.")
    data = json.loads(skills_json.read_text(encoding="utf-8"))
    entries = data.get("skills") if isinstance(data, dict) else data
    if isinstance(entries, list):
        entries = {e.get("handle") or e.get("name"): e for e in entries}

    entry = entries.get(handle)
    if not entry:
        raise RuntimeError(
            f"{handle} not in Registry.\n"
            f"  Try one of:\n"
            f"    · pass a GitHub URL directly:  commando install <url>\n"
            f"    · paste manually:               commando install --paste\n"
            f"    · PR to add it:                 edit skills.json"
        )
    if entry.get("status") != "available":
        raise RuntimeError(
            f"{handle} is status: {entry.get('status', '?')}\n"
            f"  Not yet importable. Either:\n"
            f"    · pass the upstream URL directly:  commando install <url>\n"
            f"    · wait for it to be marked 'available' in skills.json"
        )

    source_url = entry.get("source_url")
    if not source_url:
        raise RuntimeError(f"{handle} has no source_url in Registry.")
    return _fetch_url(source_url), entry


def _fetch_git(spec: str) -> str:
    """git+https://github.com/owner/repo#path/to/SKILL.md"""
    spec = spec[len("git+"):]
    if "#" in spec:
        url, subpath = spec.split("#", 1)
    else:
        raise RuntimeError("git+ source must include #path/to/SKILL.md")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "clone", "--depth", "1", url, td],
                       check=True, capture_output=True)
        return (Path(td) / subpath).read_text(encoding="utf-8")


def _fetch_local(path: str) -> str:
    if path.startswith("file://"):
        path = path[7:]
    return Path(path).expanduser().resolve().read_text(encoding="utf-8")


def _fetch_paste() -> str:
    click.echo()
    click.echo("  Paste your SKILL.md content below. End with Ctrl-D (or Ctrl-Z on Windows):")
    click.echo()
    return sys.stdin.read()


def _resolve(source: str, paste: bool) -> Tuple[str, str, Optional[dict]]:
    """Returns (content, source_label, registry_entry_or_none)."""
    if paste or source in (None, ""):
        if not paste:
            # interactive: ask which path
            click.echo()
            click.echo("  How are you adding this Skill?")
            click.echo("    1) Registry handle  (e.g. @frank-pu/xhs-bilingual-bridge)")
            click.echo("    2) GitHub URL       (e.g. https://github.com/…/SKILL.md)")
            click.echo("    3) Local file path  (e.g. ./skills/foo/SKILL.md)")
            click.echo("    4) Paste content    (open stdin)")
            click.echo()
            choice = click.prompt("  Pick 1-4", type=click.Choice(["1", "2", "3", "4"]))
            if choice == "4":
                content = _fetch_paste()
                return content, "pasted-content", None
            source = click.prompt("  Source", type=str).strip()
        else:
            content = _fetch_paste()
            return content, "pasted-content", None

    stype = _detect_source_type(source)
    if stype == "registry":
        content, entry = _fetch_registry(source)
        return content, source, entry
    if stype == "url":
        return _fetch_url(source), _normalize_github_url(source), None
    if stype == "git":
        return _fetch_git(source), source, None
    if stype == "local":
        return _fetch_local(source), source, None
    raise RuntimeError(f"unrecognized source: {source}")


# ──────────────────────────────────────────────────────────────────────────────
# SKILL.md parse / write helpers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_skill(content: str) -> Tuple[dict, str]:
    import yaml
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    try:
        fm = yaml.safe_load(content[4:end]) or {}
    except Exception:
        fm = {}
    return fm, content[end + 5:]


def _write_skill(path: Path, frontmatter: dict, body: str) -> None:
    import yaml
    fm_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n\n{body.lstrip()}\n", encoding="utf-8")


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return s or "untitled-skill"


# ──────────────────────────────────────────────────────────────────────────────
# Schedule task append (preserves comments)
# ──────────────────────────────────────────────────────────────────────────────

def _suggest_cron(frontmatter: dict) -> Optional[str]:
    tags = frontmatter.get("tags") or []
    tags = [t.lower() for t in tags]
    if "daily" in tags or "scan" in tags or "morning" in tags:
        return "0 8 * * *"          # daily 08:00
    if "weekly" in tags or "reflection" in tags:
        return "0 16 * * 5"         # Friday 16:00
    if "monthly" in tags or "seo" in tags:
        return "0 9 1 * *"          # 1st 09:00
    if "manual" in tags or "ad-hoc" in tags or "adhoc" in tags:
        return None
    return "0 8 * * *"              # default daily 08:00


def _append_task_to_schedule(schedule_yml: Path, skill_name: str,
                             frontmatter: dict, cron: Optional[str]) -> str:
    """Append a task block to schedule.yaml as text (preserves comments)."""
    task_id = re.sub(r"-", "_", skill_name)
    name = frontmatter.get("description", skill_name).split("。")[0][:60]
    if cron:
        block = (
            f"\n  - id: {task_id}\n"
            f"    name: {name}\n"
            f"    enabled: true\n"
            f"    trigger:\n"
            f"      type: cron\n"
            f"      cron: \"{cron}\"\n"
            f"    skills: [{skill_name}]\n"
            f"    outputs:\n"
            f"      notification: im_card\n"
            f"    tags: [imported]\n"
        )
    else:
        block = (
            f"\n  - id: {task_id}\n"
            f"    name: {name}\n"
            f"    enabled: true\n"
            f"    trigger:\n"
            f"      type: manual\n"
            f"    skills: [{skill_name}]\n"
            f"    outputs:\n"
            f"      notification: im_card\n"
            f"    tags: [imported, ad-hoc]\n"
        )

    text = schedule_yml.read_text(encoding="utf-8").rstrip() + "\n" + block
    schedule_yml.write_text(text, encoding="utf-8")
    return task_id


# ──────────────────────────────────────────────────────────────────────────────
# Main flow
# ──────────────────────────────────────────────────────────────────────────────

def run(source: str, target: str, paste: bool, no_rebuild: bool,
        no_schedule: bool, yes: bool) -> None:
    agent_dir = Path(target).resolve()

    click.echo()
    click.secho("  commando install", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo(f"  agent dir : {agent_dir}")

    if not agent_dir.exists():
        click.secho(f"\n  ✗ {agent_dir} doesn't exist. Run `commando init` or `commando onboard` first.", fg="red")
        sys.exit(2)

    # ── Step 1 · Resolve source ──────────────────────────────────────────────
    click.echo()
    click.secho("  Step 1 · Resolve source", bold=True)
    try:
        content, source_label, registry_entry = _resolve(source, paste)
    except Exception as e:
        click.secho(f"\n  ✗ {e}", fg="red")
        sys.exit(2)
    click.secho(f"    ✓ got SKILL.md from: {source_label[:80]}", fg="green")
    click.secho(f"      ({len(content)} chars)", fg="bright_black")

    # ── Step 2 · Parse + record provenance ──────────────────────────────────
    click.echo()
    click.secho("  Step 2 · Parse + record provenance", bold=True)
    fm, body = _parse_skill(content)
    if not fm:
        click.secho("    ✗ SKILL.md missing frontmatter (no `---` block).", fg="red")
        sys.exit(2)
    name = fm.get("name") or _slugify(fm.get("description", "untitled"))
    fm["name"] = name
    fm["source"] = source_label
    click.secho(f"    ✓ name = {name}", fg="green")
    click.secho(f"      description: {(fm.get('description') or '')[:80]}", fg="bright_black")

    # ── Step 3 · Drop into my-agent/skills/<name>/ ───────────────────────────
    click.echo()
    click.secho("  Step 3 · Install to my-agent/skills/", bold=True)
    skill_dir = agent_dir / "skills" / name
    skill_path = skill_dir / "SKILL.md"
    if skill_path.exists():
        click.secho(f"    ! {skill_path} already exists.", fg="yellow")
        if not (yes or click.confirm("    Overwrite?", default=False)):
            click.secho("    aborted.", fg="yellow")
            sys.exit(1)
    skill_dir.mkdir(parents=True, exist_ok=True)
    _write_skill(skill_path, fm, body)
    click.secho(f"    ✓ wrote {skill_path}", fg="green")

    # ── Step 4 · Offer rebuild for THIS agent's Charter ──────────────────────
    click.echo()
    click.secho("  Step 4 · Adapt to your Charter?", bold=True)
    click.echo()
    upstream_status = fm.get("status", "draft")
    if no_rebuild:
        click.secho("    ⊘ skipped per --no-rebuild", fg="bright_black")
    elif upstream_status == "active":
        # Upstream already has a complete body; rebuild only if user is explicit.
        click.echo(f"    ⊘ upstream is already status: active — keeping its body as-is.")
        click.echo(f"      (Run `commando build-skills --skill {name} --force --apply` later")
        click.echo(f"       if you decide you DO want to adapt it to your Charter.)")
    else:
        click.echo("    This Skill is a draft scaffold. Its prompt body should be authored")
        click.echo("    against YOUR Charter so voice / red lines / ICP match.")
        click.echo()
        if yes or click.confirm("    Rebuild prompt body for this agent now?", default=True):
            click.echo()
            from commando.build_skills import run as _build
            _build(str(agent_dir), skill_id=name, apply=True, force=True)
        else:
            click.secho("    skipped (keep upstream body as-is)", fg="bright_black")

    # ── Step 5 · Schedule integration ────────────────────────────────────────
    click.echo()
    click.secho("  Step 5 · Add to schedule.yaml?", bold=True)
    click.echo()
    schedule_yml = agent_dir / "schedule.yaml"
    if no_schedule:
        click.secho("    ⊘ skipped per --no-schedule", fg="bright_black")
    elif not schedule_yml.exists():
        click.secho(f"    ⊘ no schedule.yaml at {schedule_yml} — skipping", fg="bright_black")
    else:
        suggested_cron = _suggest_cron(fm)
        if suggested_cron:
            click.echo(f"    Suggested trigger (from tags {fm.get('tags') or []}):")
            click.echo(f"      cron: {suggested_cron}")
        else:
            click.echo("    Suggested trigger: manual (ad-hoc — fire with `commando run --task <id>`)")
        click.echo()
        if yes or click.confirm("    Add a task to schedule.yaml using this trigger?", default=True):
            task_id = _append_task_to_schedule(schedule_yml, name, fm, suggested_cron)
            click.secho(f"    ✓ added task '{task_id}' to {schedule_yml.name}", fg="green")
            if suggested_cron:
                click.echo()
                click.echo("    To activate it on launchd:")
                click.echo("      commando schedule install --apply")
        else:
            click.secho("    skipped (you can add it manually later)", fg="bright_black")

    # ── Step 6 · Summary ─────────────────────────────────────────────────────
    click.echo()
    click.secho("  ─── Installed ───", fg="green", bold=True)
    click.echo()
    click.echo(f"    Skill:    {name}")
    click.echo(f"    Source:   {source_label[:80]}")
    click.echo(f"    Location: {skill_path}")
    click.echo()
    click.echo("    Next:")
    click.echo(f"      commando run --task <task_id> --apply   # test it")
    click.echo(f"      commando schedule install --apply       # activate cron")
    click.echo(f"      commando status                         # see what's loaded")
    click.echo()

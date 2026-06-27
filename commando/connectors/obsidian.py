"""Obsidian connector — write markdown files to a local Obsidian vault.

Obsidian is filesystem-based; an Obsidian vault is just a folder of `.md`
files. There's no API, no auth, no network — this connector is the
simplest possible: read the vault path from credentials, write a markdown
file there.

Usage from a skill:
    from commando.connectors.obsidian import write_doc, is_configured

    if is_configured(agent_dir):
        write_doc(
            agent_dir=agent_dir,
            folder="weekly-reflections",
            filename="2026-W26",
            content="# This week\n\n…",
            frontmatter={"tags": ["reflection"], "date": "2026-06-27"},
        )
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


def _load_config(agent_dir: Path) -> Optional[dict]:
    """Read credentials/obsidian.yaml. Returns None if not configured."""
    cred = agent_dir / "credentials" / "obsidian.yaml"
    if not cred.exists():
        return None
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(cred.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not data.get("vault_path"):
        return None
    return data


def is_configured(agent_dir: Path) -> bool:
    """True iff a usable Obsidian vault is configured for this agent."""
    cfg = _load_config(agent_dir)
    if not cfg:
        return False
    vault = Path(cfg["vault_path"]).expanduser()
    return vault.exists() and vault.is_dir()


def get_vault_path(agent_dir: Path) -> Optional[Path]:
    """Return the expanded absolute vault path, or None if unconfigured."""
    cfg = _load_config(agent_dir)
    if not cfg:
        return None
    return Path(cfg["vault_path"]).expanduser().resolve()


def get_default_folder(agent_dir: Path) -> str:
    """Folder inside the vault where commando outputs land by default."""
    cfg = _load_config(agent_dir)
    return (cfg or {}).get("default_folder", "commando")


def _sanitize_filename(name: str) -> str:
    """Strip characters illegal on macOS/Linux/Windows in filenames."""
    for ch in "/\\:*?\"<>|":
        name = name.replace(ch, "-")
    return name.strip().strip(".") or "untitled"


def write_doc(
    agent_dir: Path,
    folder: str,
    filename: str,
    content: str,
    frontmatter: Optional[dict] = None,
) -> Optional[Path]:
    """Write a markdown doc to vault/<folder>/<filename>.md.

    Returns the written file path on success, None if Obsidian isn't
    configured.

    If `frontmatter` is provided, it's prepended as a YAML block — making
    the doc usable with Obsidian Properties and Dataview queries.

    Idempotency: if the target file already exists, a numeric suffix
    `-2`, `-3`, … is appended so we never silently overwrite the user's
    work.
    """
    vault = get_vault_path(agent_dir)
    if vault is None:
        return None

    target_dir = vault / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_filename(filename)
    target = target_dir / f"{safe_name}.md"
    suffix = 2
    while target.exists():
        target = target_dir / f"{safe_name}-{suffix}.md"
        suffix += 1

    body = content
    if frontmatter:
        try:
            import yaml  # type: ignore
            fm_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
            body = f"---\n{fm_text}---\n\n{content.lstrip()}"
        except Exception:
            # If yaml isn't available, append frontmatter as comments
            lines = [f"<!-- {k}: {v} -->" for k, v in frontmatter.items()]
            body = "\n".join(lines) + "\n\n" + content

    target.write_text(body, encoding="utf-8")
    return target


def write_event(agent_dir: Path, event: dict) -> Optional[Path]:
    """Convenience for routing an episodic-event-shaped dict to Obsidian.

    Used by the dashboard's auto-route when 'documents.provider: obsidian'
    is declared in connectors.yaml — turns any episodic event with a
    'message' or 'content' field into a dated note under the agent's
    folder in the vault.
    """
    cfg = _load_config(agent_dir)
    if not cfg:
        return None

    ts = event.get("ts", datetime.now().isoformat())
    skill = event.get("skill", "agent")
    folder = cfg.get("default_folder", "commando")

    date_part = ts[:10] if len(ts) >= 10 else datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_part}-{skill}"
    content = event.get("content") or event.get("message") or str(event)

    return write_doc(
        agent_dir=agent_dir,
        folder=folder,
        filename=filename,
        content=content,
        frontmatter={
            "skill": skill,
            "ts": ts,
            "level": event.get("level"),
            "tags": ["commando", skill],
        },
    )

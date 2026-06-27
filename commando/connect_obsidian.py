"""commando connect obsidian — interactive wizard.

Obsidian is filesystem-based: a vault is just a folder of markdown files.
So this wizard is trivial compared to the Feishu IM one — no auth, no
network, no platform-side configuration. Just:

  Step 1 · find or pick the user's Obsidian vault
  Step 2 · ask for a default subfolder for commando outputs
  Step 3 · write my-agent/credentials/obsidian.yaml
  Step 4 · test write — drop a hello.md into the vault and verify

Result: skills + dashboard can now use commando.connectors.obsidian to
write docs into the user's vault.
"""

from pathlib import Path
from typing import List, Optional

import click


# ──────────────────────────────────────────────────────────────────────────────
# UI helpers (matched to connect_im_feishu.py)
# ──────────────────────────────────────────────────────────────────────────────

def _h1(text: str) -> None:
    click.echo()
    click.secho(f"  {text}", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")


def _step(n: int, title: str) -> None:
    click.echo()
    click.secho(f"  Step {n} · {title}", bold=True)


def _ok(msg: str) -> None:
    click.secho(f"    ✓ {msg}", fg="green")


def _warn(msg: str) -> None:
    click.secho(f"    ! {msg}", fg="yellow")


def _err(msg: str) -> None:
    click.secho(f"    ✗ {msg}", fg="red")


def _dim(msg: str) -> None:
    click.secho(f"    {msg}", fg="bright_black")


# ──────────────────────────────────────────────────────────────────────────────
# Vault discovery
# ──────────────────────────────────────────────────────────────────────────────

def _looks_like_vault(p: Path) -> bool:
    """An Obsidian vault has a hidden .obsidian/ directory."""
    return p.exists() and p.is_dir() and (p / ".obsidian").exists()


def _discover_vaults() -> List[Path]:
    """Scan well-known locations for Obsidian vaults.

    Obsidian doesn't expose a CLI / config file at a fixed location, but
    most users keep their vaults in iCloud, Documents, or ~/. We look at
    common spots and dedupe."""
    home = Path.home()
    candidates_roots = [
        home / "Documents",
        home / "Obsidian",
        home / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents",
        home,
    ]
    found: List[Path] = []
    for root in candidates_roots:
        if not root.exists():
            continue
        try:
            # Look at the root itself and its immediate subdirectories
            if _looks_like_vault(root):
                found.append(root.resolve())
            for child in root.iterdir():
                if child.is_dir() and _looks_like_vault(child):
                    found.append(child.resolve())
        except (PermissionError, OSError):
            continue
    # Dedupe, preserve order
    seen: set = set()
    unique: List[Path] = []
    for v in found:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


def _pick_vault() -> Optional[Path]:
    _step(1, "Find your Obsidian vault")

    vaults = _discover_vaults()
    if vaults:
        click.echo()
        click.echo("  Found these existing vaults:")
        click.echo()
        for i, v in enumerate(vaults, 1):
            click.echo(f"    [{i}]  {v}")
        click.echo(f"    [m]  ... enter a path manually")
        click.echo()
        choice = click.prompt("  Pick one", type=str).strip().lower()
        if choice == "m":
            return _prompt_manual()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(vaults):
                return vaults[idx]
        except ValueError:
            pass
        _warn("invalid choice, falling back to manual entry")
        return _prompt_manual()

    _warn("no Obsidian vault auto-detected in common locations")
    click.echo()
    click.echo("  Common reasons:")
    click.echo("    · You keep your vault somewhere unusual (e.g. an external drive)")
    click.echo("    · You haven't created an Obsidian vault yet")
    click.echo("      → if so, open Obsidian, create a vault, then re-run this")
    click.echo()
    return _prompt_manual()


def _prompt_manual() -> Optional[Path]:
    raw = click.prompt("  Vault path", type=str, default="", show_default=False).strip()
    if not raw:
        _err("no path given")
        return None
    p = Path(raw).expanduser().resolve()
    if not p.exists():
        _err(f"path does not exist: {p}")
        if click.confirm(f"  Create directory {p} now?", default=False):
            p.mkdir(parents=True, exist_ok=True)
            _ok(f"created {p}")
        else:
            return None
    if not p.is_dir():
        _err(f"not a directory: {p}")
        return None
    if not _looks_like_vault(p):
        _warn(f"{p} doesn't look like an Obsidian vault (no .obsidian/ subdir)")
        if not click.confirm("  Use it anyway?", default=False):
            return None
    return p


# ──────────────────────────────────────────────────────────────────────────────
# Folder + credentials
# ──────────────────────────────────────────────────────────────────────────────

def _pick_folder(vault: Path) -> str:
    _step(2, "Pick a folder inside the vault for commando outputs")
    click.echo()
    click.echo("  commando will create + write into this folder, leaving the rest")
    click.echo("  of your vault untouched. Recommended: 'commando' (we'll create it).")
    click.echo()
    folder = click.prompt("  Folder name", type=str, default="commando").strip().strip("/")
    target = vault / folder
    if target.exists() and not target.is_dir():
        _err(f"{target} exists but is not a directory")
        raise click.Abort()
    return folder


def _write_credentials(agent_dir: Path, vault: Path, folder: str) -> Path:
    _step(3, "Write credentials")
    cred_dir = agent_dir / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    cred_file = cred_dir / "obsidian.yaml"

    content = (
        "# commando — Obsidian connector\n"
        "# Written by `commando connect obsidian`. Edit any time.\n"
        f"\n"
        f"vault_path: {vault}\n"
        f"default_folder: {folder}\n"
    )
    cred_file.write_text(content, encoding="utf-8")
    _ok(f"wrote {cred_file}")
    return cred_file


# ──────────────────────────────────────────────────────────────────────────────
# Test write
# ──────────────────────────────────────────────────────────────────────────────

def _test_write(agent_dir: Path) -> None:
    _step(4, "Test write")
    from commando.connectors.obsidian import write_doc

    written = write_doc(
        agent_dir=agent_dir,
        folder=_load_folder(agent_dir),
        filename="commando-hello",
        content=(
            "# commando is connected to your Obsidian vault\n\n"
            "This file is the smoke-test. If you can read it, your\n"
            "Obsidian connector is wired up correctly — skills can now\n"
            "drop docs here automatically.\n\n"
            "Feel free to delete this file. commando won't recreate it.\n"
        ),
        frontmatter={"source": "commando", "type": "smoke-test"},
    )
    if written is None:
        _err("write returned None — credentials file may be malformed")
        raise click.Abort()
    _ok(f"wrote test file: {written}")
    click.echo()
    _dim("Open Obsidian → you should see this file in the folder you picked.")


def _load_folder(agent_dir: Path) -> str:
    from commando.connectors.obsidian import get_default_folder
    return get_default_folder(agent_dir)


# ──────────────────────────────────────────────────────────────────────────────
# Main entry
# ──────────────────────────────────────────────────────────────────────────────

def run(target: str = "./my-agent") -> None:
    agent_dir = Path(target).resolve()
    _h1("commando connect obsidian")
    click.echo()
    click.echo(f"  agent dir : {agent_dir}")

    if not agent_dir.exists():
        _err(f"{agent_dir} doesn't exist. Run `commando init` or `commando onboard` first.")
        raise click.Abort()

    vault = _pick_vault()
    if vault is None:
        _err("no vault selected — aborting")
        raise click.Abort()
    _ok(f"vault: {vault}")

    folder = _pick_folder(vault)
    _ok(f"folder inside vault: {folder}")

    _write_credentials(agent_dir, vault, folder)
    _test_write(agent_dir)

    click.echo()
    click.secho("  ─── Connected ───", fg="green", bold=True)
    click.echo()
    click.echo("  What changed:")
    click.echo(f"    · Skills that need 文档协作 (documents) now have Obsidian as their backend")
    click.echo(f"    · commando dashboard will show Obsidian as connected")
    click.echo(f"    · Outputs land in: {vault}/{folder}/")
    click.echo()
    click.echo("  Smoke test:")
    click.echo(f"    commando status   # should show 'Obsidian: ok'")
    click.echo()

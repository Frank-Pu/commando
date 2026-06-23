"""commando connect im-feishu — interactive wizard.

Setup flow (chronological from user's POV):
  Step 1 · check lark-cli installed
  Step 2 · pick an App ID (reuse logged-in app OR add a new one)
  Step 3 · auth (skipped if already logged in for that app)
  Step 4 · resolve user open_id (auto from ~/.lark-cli/config.json)
  Step 5 · send a test ping via --user-id → captures chat_id from response
  Step 6 · write my-agent/credentials/feishu.yaml
  Step 7 · send the v0.1 "waiting" demo card to verify end-to-end

Trust assumptions (user must have done these via Feishu开放平台 UI):
  - created a self-built app
  - granted im:message:send_as_bot scope
  - published a version
  - added the bot to their own Feishu workspace

These can't be automated (they're UI clicks in Feishu开放平台). The wizard
hands the user a deep link to open.feishu.cn/app if they haven't done it.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

import click

REPO_ROOT = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────────────────
# UI helpers
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
# Step 1 · lark-cli detection
# ──────────────────────────────────────────────────────────────────────────────

def _check_lark_cli() -> None:
    _step(1, "Detecting lark-cli")
    path = shutil.which("lark-cli")
    if path is None:
        _err("lark-cli not in PATH")
        click.echo()
        click.echo("    Install one of:")
        click.echo("      brew install lark-cli                          # macOS")
        click.echo("      npm install -g @larksuiteoapi/lark-cli         # cross-platform")
        click.echo()
        click.echo("    Then re-run: commando connect im-feishu")
        sys.exit(2)
    _ok(f"found at {path}")


# ──────────────────────────────────────────────────────────────────────────────
# Step 2 · pick / add app
# ──────────────────────────────────────────────────────────────────────────────

def _read_lark_config() -> dict:
    cfg = Path.home() / ".lark-cli" / "config.json"
    if not cfg.exists():
        return {}
    try:
        return json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _logged_in_apps() -> list:
    cfg = _read_lark_config()
    out = []
    for app in (cfg.get("apps") or []):
        users = app.get("users") or []
        if users:
            out.append({
                "appId": app.get("appId"),
                "name": app.get("name") or "",
                "userOpenId": users[0].get("userOpenId"),
                "userName": users[0].get("userName") or "(unknown)",
            })
    return out


def _pick_app() -> Tuple[str, str]:
    """Returns (app_id, user_open_id). Either reuses a logged-in app or adds a new one."""
    _step(2, "Choosing a Feishu app")

    existing = _logged_in_apps()
    if existing:
        click.echo(f"    Found {len(existing)} app(s) already authed via lark-cli:")
        for i, a in enumerate(existing):
            label = a["name"] or "(unnamed)"
            click.echo(f"      [{i + 1}] {a['appId']}  · {label}  · as {a['userName']}")
        click.echo(f"      [{len(existing) + 1}] add a new app")
        choice = click.prompt("    Pick", type=click.IntRange(1, len(existing) + 1), default=1)
        if choice <= len(existing):
            sel = existing[choice - 1]
            _ok(f"reusing {sel['appId']}")
            return sel["appId"], sel["userOpenId"]

    # add a new app
    click.echo()
    click.echo("    Get App ID + App Secret from:")
    click.secho("      https://open.feishu.cn/app  →  your bot app  →  Credentials", fg="blue")
    click.echo()
    click.echo("    Prerequisites (do these in Feishu开放平台 if you haven't):")
    click.echo("      1) Create a self-built app")
    click.echo("      2) Grant scope: im:message:send_as_bot")
    click.echo("      3) Publish a version")
    click.echo("      4) Add the bot to your own Feishu workspace")
    click.echo("    Full guide: docs/feishu-im-setup.md")
    click.echo()

    app_id = click.prompt("    App ID (cli_...)", type=str).strip()
    if not app_id.startswith("cli_"):
        _warn(f"App ID should start with 'cli_' (got '{app_id[:20]}...')")
        if not click.confirm("    Continue anyway?", default=False):
            sys.exit(1)

    app_secret = click.prompt("    App Secret", type=str, hide_input=True).strip()

    _step(3, "Running lark-cli auth login")
    _dim(f"lark-cli auth login --app-id {app_id} --app-secret <hidden>")
    r = subprocess.run(
        ["lark-cli", "auth", "login", "--app-id", app_id, "--app-secret", app_secret],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        _err(f"login failed (rc={r.returncode})")
        click.echo(f"      {(r.stderr or r.stdout).strip()[:400]}")
        sys.exit(2)
    _ok("authed")

    # re-read config to find the user_open_id
    new = _logged_in_apps()
    for a in new:
        if a["appId"] == app_id:
            return app_id, a["userOpenId"]

    _err("login succeeded but user_open_id not found in lark-cli config")
    sys.exit(2)


# ──────────────────────────────────────────────────────────────────────────────
# Step 4 · send + capture chat_id
# ──────────────────────────────────────────────────────────────────────────────

def _send_and_capture(app_id: str, user_open_id: str) -> Optional[str]:
    """Send a ping via --user-id; return chat_id parsed from response."""
    _step(4, "Sending a ping to discover your DM chat_id")
    _dim(f"lark-cli --profile {app_id} im +messages-send --as bot --user-id {user_open_id[:24]}…")

    env = {**os.environ, "LARK_CLI_NO_PROXY": "1"}
    r = subprocess.run(
        ["lark-cli", "--profile", app_id, "im", "+messages-send",
         "--as", "bot", "--user-id", user_open_id,
         "--text", "👋 commando connect im-feishu · 联调中"],
        capture_output=True, text=True, env=env,
    )

    if r.returncode != 0:
        _err(f"send failed (rc={r.returncode})")
        click.echo(f"      {(r.stderr or r.stdout).strip()[:400]}")
        click.echo()
        click.echo("    Common causes:")
        click.echo("      · bot version not published (Step 5 of docs/feishu-im-setup.md)")
        click.echo("      · scope im:message:send_as_bot not granted")
        click.echo("      · bot not added to your Feishu workspace (Step 6)")
        return None

    try:
        json_start = r.stdout.find("{")
        data = json.loads(r.stdout[json_start:]) if json_start >= 0 else {}
    except json.JSONDecodeError:
        _err("response is not valid JSON")
        _dim(r.stdout[:400])
        return None

    if not data.get("ok"):
        _err(f"API error: {json.dumps(data.get('error', {}), ensure_ascii=False)[:300]}")
        return None

    chat_id = (data.get("data") or {}).get("chat_id")
    if not chat_id:
        _err("response did not include chat_id")
        return None

    _ok(f"chat_id captured: {chat_id[:24]}…")
    _dim("(check your Feishu — you should see the ping message)")
    return chat_id


# ──────────────────────────────────────────────────────────────────────────────
# Step 5 · write credentials
# ──────────────────────────────────────────────────────────────────────────────

def _write_credentials(app_id: str, chat_id: str) -> Path:
    _step(5, "Writing credentials")

    cwd = Path.cwd()
    cred_dir = cwd / "my-agent" / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    cred_path = cred_dir / "feishu.yaml"

    rel = cred_path.relative_to(cwd) if cred_path.is_relative_to(cwd) else cred_path

    if cred_path.exists():
        click.echo()
        if not click.confirm(f"    {rel} exists. Overwrite?", default=True):
            _warn("leaving existing file untouched")
            return cred_path

    content = (
        f"# auto-generated by `commando connect im-feishu`\n"
        f"# app_secret stays in macOS Keychain (managed by lark-cli) — not written here.\n"
        f"bot_app:\n"
        f"  app_id: {app_id}\n"
        f"  notify_chat_id: {chat_id}\n"
    )
    cred_path.write_text(content, encoding="utf-8")
    _ok(f"wrote {rel}")
    return cred_path


# ──────────────────────────────────────────────────────────────────────────────
# Step 6 · verify by sending the v0.1 demo card
# ──────────────────────────────────────────────────────────────────────────────

def _verify_with_demo() -> None:
    _step(6, "Sending the v0.1 'waiting' demo card to verify")

    route_script = REPO_ROOT / "tools" / "route.py"
    if not route_script.exists():
        _warn("tools/route.py not found — skipping demo")
        return

    env = {**os.environ, "LARK_CLI_NO_PROXY": "1"}
    r = subprocess.run(
        [sys.executable, str(route_script), "--demo", "waiting", "--apply",
         "--agent-dir", str(Path.cwd() / "my-agent")],
        capture_output=True, text=True, env=env,
    )
    if "✓ sent" in r.stdout:
        _ok("demo card sent — check your Feishu DM (yellow waiting-for-review card)")
    else:
        _warn("demo send did not return ✓")
        _dim(r.stdout[-300:].strip())
        _dim((r.stderr or "")[-200:].strip())


# ──────────────────────────────────────────────────────────────────────────────
# Final
# ──────────────────────────────────────────────────────────────────────────────

def _success() -> None:
    click.echo()
    click.secho("  ✓ Setup complete.", fg="green", bold=True)
    click.echo()
    click.echo("  Try these commands now:")
    click.echo("    commando route --demo im --apply       · agent speaks")
    click.echo("    commando route --demo done --apply     · task done")
    click.echo("    commando route --demo morning --apply  · morning brief")
    click.echo()
    click.echo("  Edit routing rules: my-agent/event-routing.yaml")
    click.echo("  Edit routing docs:  docs/event-bus.md")
    click.echo()


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────────────────────────────────────

def run() -> None:
    _h1("commando connect im-feishu")
    click.echo()
    click.echo("  We'll wire your Feishu bot to commando in ~3 minutes.")
    click.echo("  No need to find chat_id manually — we capture it from the first send.")

    _check_lark_cli()
    app_id, user_open_id = _pick_app()
    chat_id = _send_and_capture(app_id, user_open_id)
    if not chat_id:
        click.echo()
        click.secho("  ✗ Setup aborted. See errors above.", fg="red")
        sys.exit(2)

    _write_credentials(app_id, chat_id)
    _verify_with_demo()
    _success()

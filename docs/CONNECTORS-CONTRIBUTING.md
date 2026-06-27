# Contributing a connector

commando connects to external services through small Python modules called **connectors**. Each connector is dead simple — typically 50–200 lines — and follows the same shape. This doc walks through the shape using **Obsidian** as the reference implementation, then shows how to PR a new one.

If you've been waiting for **Slack**, **Notion**, **Stripe**, **Gmail**, **Discord**, or anything else — this is your invitation.

---

## The mental model

commando is deliberately **not a plugin system**. There is no `register_connector(...)` API, no manifest, no lifecycle hooks. A connector is just two or three small files that follow a convention. Skills import the driver directly when they need it.

```
commando/connectors/<name>.py       ← runtime driver (the actual code)
commando/connect_<name>.py          ← interactive `commando connect <name>` wizard
my-agent/credentials/<name>.yaml    ← written by the wizard, read by the driver
```

That's it. Three files. No magic.

---

## What a connector must do

Pick one or both:

| Direction | What it means | Example |
|---|---|---|
| **Write (output)** | Skills produce content; the connector delivers it somewhere | Obsidian (write `.md` to vault), Notion (create page), Slack (send message), Gmail (send mail) |
| **Read (input)** | Skills need data; the connector fetches it | Stripe (recent charges), Gmail (unread messages), Notion (database rows) |

Most v0.1 connectors are write-only — easier to implement, easier to verify. Read-side requires careful auth + rate-limit thinking.

---

## The driver contract (`commando/connectors/<name>.py`)

The driver exposes a small functional API. **No classes required.** Two functions are mandatory; others are connector-specific.

```python
# Mandatory — every connector implements these two

def is_configured(agent_dir: Path) -> bool:
    """Return True iff the agent has working credentials for this connector.
    Used by `commando status`, the dashboard, and Skill conditional logic."""

def _load_config(agent_dir: Path) -> Optional[dict]:
    """Read credentials/<name>.yaml. Return None if missing/unparseable.
    Prefix with _ to mark internal — skills should call is_configured()."""
```

Beyond that, expose whatever functions skills need:

```python
# Write-direction example (Obsidian, Notion, Slack)
def write_doc(agent_dir: Path, folder: str, filename: str, content: str,
              frontmatter: Optional[dict] = None) -> Optional[Path]:
    """Return path/URL on success, None if not configured."""

# Read-direction example (Stripe, Gmail)
def fetch_recent(agent_dir: Path, window_days: int = 7) -> Optional[list[dict]]:
    """Return data on success, None if not configured."""
```

**Key principles for driver code**:

1. **Idempotent writes.** Don't silently overwrite the user's data. If a target exists, suffix `-2`, `-3`, … (see `obsidian.py:_sanitize_filename`).
2. **Return `None` when unconfigured** — let the caller's `if Connectors Available` branch decide what to do.
3. **No side effects on import.** Network calls, file ops, anything that could fail belongs inside functions.
4. **Be cheap to call.** `is_configured()` runs every dashboard refresh — should not hit the network. Read the yaml and check fields, no more.
5. **One exception family.** Convert third-party SDK exceptions into clean `RuntimeError` with helpful messages.

---

## The wizard contract (`commando/connect_<name>.py`)

The wizard is what runs when a user types `commando connect <name>`. Its job is to gather whatever the driver needs and write `credentials/<name>.yaml`.

Required shape:

```python
def run(target: str = "./my-agent") -> None:
    """Interactive setup. Writes credentials/<name>.yaml. Raises click.Abort on failure."""
```

Wizards typically follow this 4-step pattern (see `connect_obsidian.py` or `connect_im_feishu.py`):

```
Step 1 · Discover / pick — auto-detect vaults, logged-in app IDs, etc.
Step 2 · Configure       — ask for the few fields the driver needs
Step 3 · Write           — drop the yaml into credentials/
Step 4 · Test            — actually try a write (or read) end-to-end so the
                          user sees something real on the platform
```

Use `commando/connect_im_feishu.py` (complex — handles OAuth, app picking, bot token capture) and `commando/connect_obsidian.py` (minimal — just a folder picker) as the two reference points. Most platforms fall somewhere between.

---

## Credentials file format

YAML, one file per connector at `<agent>/credentials/<name>.yaml`. The wizard writes it; the driver reads it.

```yaml
# commando — <Name> connector
# Written by `commando connect <name>`. Edit any time.

# Required fields (whatever your driver needs)
api_key: "sk-..."
workspace_id: "..."

# Optional sensible defaults
default_folder: "commando"
timeout_seconds: 30
```

**Never commit `credentials/`** — it's already in commando's `.gitignore` at the agent level. The wizard should ASCII-art warn if it detects the user is about to.

---

## Status integration (~3 lines)

So `commando status` and the dashboard surface the new connector, append one entry in two files:

```python
# dashboard/server.py — read_connectors_status()
known = [
    ...,
    ("<slug>", "<Display Name>", "<key_field_to_check>"),
]
```

```python
# commando/status.py — run() function, Connectors section
cred = agent_dir / "credentials" / "<name>.yaml"
if cred.exists() and _check(cred):
    click.echo(_ok(f"<Display>: {cred}"))
else:
    click.echo(_dim("<Display>: not configured — `commando connect <name>` (optional)"))
```

That's the full integration surface. No registration, no metadata file.

---

## The PR checklist

When you open the PR, please confirm:

- [ ] `commando/connectors/<name>.py` with `is_configured()` + at least one write-side or read-side function
- [ ] `commando/connect_<name>.py` with an interactive `run(target)` wizard
- [ ] CLI subcommand wired in `commando/cli.py` (one block of ~6 lines)
- [ ] Status check added in `dashboard/server.py:read_connectors_status` and `commando/status.py`
- [ ] Smoke test passes (paste the terminal output in the PR)
- [ ] If the platform has rate limits — driver respects them (no spam during testing)
- [ ] No secrets / personal tokens in the test output you paste

---

## The reference example: Obsidian

Obsidian is the cleanest possible connector — no API, no auth, no network. Just markdown files on the user's filesystem.

| File | Lines | What it does |
|---|---|---|
| [`commando/connectors/obsidian.py`](../commando/connectors/obsidian.py) | ~140 | Driver — `write_doc()`, `is_configured()`, `write_event()` |
| [`commando/connect_obsidian.py`](../commando/connect_obsidian.py) | ~200 | Wizard — discovers vaults, picks folder, writes creds, test-writes a hello file |
| [`commando/cli.py`](../commando/cli.py) (`connect_obsidian`) | 6 | CLI wiring |
| [`commando/status.py`](../commando/status.py) (`run`) | 12 | Status integration |

Read these four small chunks of code in order — that's the entire pattern.

---

## Patterns by integration type

### Pattern A — Local filesystem (Obsidian, generic files)
Simplest. No auth, no network. Just write to a path the user picked. **30 minutes to build.**

### Pattern B — Single webhook URL (Slack, Discord, generic webhooks)
User pastes a webhook URL the platform gave them; driver POSTs JSON. No OAuth, no scope handling. **1 hour to build.**

### Pattern C — API key (Notion, Stripe, OpenAI, ZhipuAI)
User pastes an API key generated on the platform's dashboard; driver hits REST endpoints with `Authorization: Bearer ...`. Some need workspace/account IDs alongside the key. **1 evening to build.**

### Pattern D — OAuth (Gmail, Google Workspace, Microsoft 365)
User clicks through an OAuth flow on the wizard. Refresh tokens to manage. Platform-side scope configuration. **1-2 evenings to build, and harder to test.**

### Pattern E — Official CLI passthrough (Feishu via `lark-cli`, Stripe via `stripe-cli`)
Wizard checks the CLI is installed + logged in; driver `subprocess.run`s it. Less code than a native API integration, but adds an install dependency. **1 hour wrapper, often the right choice.**

For most platforms one of these patterns applies cleanly. Pick the simplest one that works.

---

## What we'd love to see PRs for

| Connector | Pattern | Why it matters |
|---|---|---|
| **Slack** | B (webhook) or C (Bot token) | Most-asked-for after Feishu |
| **Notion** | C (API key) or MCP server passthrough | Unlocks PKM + team workflows |
| **Stripe** | C (API key) + E (`stripe-cli`) | Finance agents (see the personas) |
| **Gmail** | D (OAuth) | "Triage my inbox" agents |
| **Discord** | B (webhook) | Community/server-running agents |
| **Linear / Jira** | C (API key) | Engineering team agents |
| **Telegram** | B (bot token URL) | Personal IM agents |
| **iCloud Reminders / Things** | A (filesystem) on macOS | Personal productivity agents |

Open an issue first if you're not sure which platform pattern fits — happy to chat through the trade-offs.

---

## License

By contributing a connector, you agree that your contribution is licensed under the MIT License — same as commando itself.

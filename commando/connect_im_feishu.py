"""commando connect im-feishu — interactive wizard for Feishu IM push setup.

v0.1 status: skeleton / coming-soon panel. v0.2 will implement the full flow:
  - check lark-cli installed
  - prompt for App ID + App Secret
  - run `lark-cli auth login`
  - prompt user to DM bot once
  - run `lark-cli im +chats-list` and parse p2p chat_id
  - write my-agent/credentials/feishu.yaml
  - send a test card and verify
"""

import click


def run() -> None:
    click.echo()
    click.secho("  commando connect im-feishu", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo("  ⏳ Interactive wizard ships in v0.2.")
    click.echo()
    click.echo("  For v0.1, follow the manual 10-step guide (~15 minutes):")
    click.secho("    docs/feishu-im-setup.md", fg="green")
    click.echo()
    click.echo("  What v0.2 will automate:")
    click.echo("    1. Detect lark-cli; if missing, suggest brew/npm install")
    click.echo("    2. Prompt App ID + App Secret (read from clipboard if possible)")
    click.echo("    3. Run `lark-cli auth login` for you")
    click.echo("    4. Tell you to DM the bot once in Feishu, then wait")
    click.echo("    5. Run `lark-cli im +chats-list`, auto-pick the p2p chat")
    click.echo("    6. Write my-agent/credentials/feishu.yaml")
    click.echo("    7. Send a test card and confirm it arrived")
    click.echo()
    click.echo("  After that, `commando route --demo waiting --apply` sends a real card.")
    click.echo()

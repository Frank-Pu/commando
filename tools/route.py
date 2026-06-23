#!/usr/bin/env python3
"""
commando route — match Episodic events against event-routing.yaml and push
to IM (default: dry-run · pass --apply to invoke lark-cli for real).

Pattern ported from atu/connectors/feishu/im.py (6 months production usage).
Card schema follows飞书 V2 (interactive, with markdown body + primary/secondary
buttons routing to artifact_uri / workbench_uri).

First-time setup: docs/feishu-im-setup.md.

Usage:
    # See what would happen with one of the 4 built-in demo events:
    python tools/route.py --demo waiting

    # Actually send (after you've finished feishu-im-setup):
    python tools/route.py --demo waiting --apply
    python tools/route.py --demo im      --apply
    python tools/route.py --demo done    --apply
    python tools/route.py --demo morning --apply

    # Process a real event from JSON file
    python tools/route.py --event-file ./event.json --apply
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.stderr.write("error: pyyaml required (pip install pyyaml)\n")
        sys.exit(2)
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        sys.stderr.write(f"warning: failed to parse {path}: {e}\n")
        return {}


def matches(event: dict, when: dict) -> bool:
    """Evaluate the rule's when clause. AND across all keys.
    Supports level=value | level=[values] | skill_in=[skills] | task_id=value."""
    for k, v in when.items():
        if k.endswith("_in"):
            base = k[:-3]
            if event.get(base) not in (v or []):
                return False
        elif isinstance(v, list):
            if event.get(k) not in v:
                return False
        else:
            if event.get(k) != v:
                return False
    return True


def humanize_ms(ms: Optional[int]) -> str:
    if not ms:
        return ""
    s = ms / 1000
    if s < 60:
        return f"{int(s)}s"
    return f"{int(s // 60)}m{int(s % 60)}s"


def render_template(tpl: str, event: dict, defaults: dict) -> str:
    fields = {**defaults, **event}
    fields["duration_human"] = humanize_ms(event.get("duration_ms"))
    fields.setdefault("artifact_uri", "#")
    fields.setdefault("workbench_uri", "#")
    fields.setdefault("agent_name", defaults.get("agent_name", event.get("agent_id", "agent")))
    try:
        return tpl.format(**fields)
    except (KeyError, IndexError):
        return tpl


def build_card(text: str, card_actions: Optional[dict], agent_name: str,
               event: dict, defaults: dict) -> dict:
    """V2 interactive card — atu pattern: buttons as top-level elements with `behaviors`."""
    elements = []

    # 主按钮放顶（最重要的 CTA 30 秒可见）
    if card_actions and card_actions.get("primary"):
        spec = card_actions["primary"]
        elements.append({
            "tag": "button",
            "text": {"tag": "plain_text",
                     "content": render_template(spec.get("text", "Open"), event, defaults)},
            "type": "primary",
            "behaviors": [{"type": "open_url",
                           "default_url": render_template(spec.get("uri", "#"), event, defaults)}],
        })
        elements.append({"tag": "hr"})

    # markdown 正文
    elements.append({"tag": "markdown", "content": text})

    # 副链接（markdown 形式，不抢主按钮焦点）
    if card_actions and card_actions.get("secondary"):
        spec = card_actions["secondary"]
        label = render_template(spec.get("text", "Details"), event, defaults)
        url = render_template(spec.get("uri", "#"), event, defaults)
        if url and url != "#":
            elements.append({"tag": "hr"})
            elements.append({"tag": "markdown", "content": f"📋 [{label}]({url})"})

    # template 色：waiting → yellow，done → green，其他 → orange
    level = event.get("level", "im")
    template_color = {"waiting": "yellow", "done": "green", "im": "blue"}.get(level, "orange")
    title_icon = {"waiting": "⏸", "done": "✅", "im": "🔔"}.get(level, "🔔")

    return {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text", "content": f"{title_icon} {agent_name}"},
            "template": template_color,
        },
        "body": {"elements": elements},
    }


def send_to_feishu(chat_id: str, card: dict, profile: Optional[str], dry: bool) -> bool:
    # lark-cli flag order: `--profile` is a GLOBAL flag, must come before subcommand
    cmd = ["lark-cli"]
    if profile:
        cmd += ["--profile", profile]
    cmd += [
        "im", "+messages-send",
        "--as", "bot",
        "--chat-id", chat_id,
        "--msg-type", "interactive",
        "--content", json.dumps(card, ensure_ascii=False),
    ]

    if dry:
        compact_cmd = " ".join(cmd[:6])
        size = len(json.dumps(card))
        print(f"     [DRY] {compact_cmd} \\")
        print(f"            --content '<v2-card json, {size} bytes>'")
        if profile:
            print(f"            --profile {profile}")
        return True

    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        sys.stderr.write("     ERROR: lark-cli not in PATH.\n")
        sys.stderr.write("            install: brew install lark-cli  (or `npm i -g @larksuiteoapi/lark-cli`)\n")
        return False

    if r.returncode != 0:
        sys.stderr.write(f"     ERROR (rc={r.returncode}): {r.stderr.strip()[:240]}\n")
        return False

    print(f"     ✓ sent · {r.stdout.strip()[:80]}")
    return True


DEMO_EVENTS = {
    "im": {
        "event_id": "demo-im",
        "level": "im",
        "agent_id": "atu",
        "agent_name": "阿土",
        "skill": "xhs-bilingual-bridge",
        "task_id": "xhs_draft_tue",
        "message": "今天选题里这条值得看一下 → reddit.com/r/languagelearning/comments/...",
        "artifact_uri": "https://www.feishu.cn/docx/example",
    },
    "waiting": {
        "event_id": "demo-waiting",
        "level": "waiting",
        "agent_id": "atu",
        "agent_name": "阿土",
        "skill": "xhs-bilingual-bridge",
        "task_id": "xhs_draft_tue",
        "message": "11:00 跑完了 · 1 篇笔记初稿 · artifact 已提交飞书 docx",
        "artifact_uri": "https://www.feishu.cn/docx/example",
        "workbench_uri": "https://www.feishu.cn/base/example",
        "duration_ms": 107000,
    },
    "done": {
        "event_id": "demo-done",
        "level": "done",
        "agent_id": "atu",
        "agent_name": "阿土",
        "skill": "marketing-effect-analysis",
        "task_id": "weekly_data_review",
        "message": "7 张图已生成 · weekly-data-report.md 已写",
        "duration_ms": 89000,
        "workbench_uri": "https://www.feishu.cn/base/example",
    },
    "morning": {
        "event_id": "demo-morning",
        "level": "done",
        "agent_id": "atu",
        "agent_name": "阿土",
        "skill": "reddit-source-mining",
        "task_id": "morning_sense",
        "message": "12 candidates · score >= 4 · 写入选题池",
        "duration_ms": 142000,
        "workbench_uri": "https://www.feishu.cn/base/example",
    },
}


def route_event(event: dict, routing: dict, credentials: dict, dry: bool) -> bool:
    rules = routing.get("rules") or []
    destinations = routing.get("destinations") or {}
    defaults = routing.get("defaults") or {}

    matched = next((r for r in rules if matches(event, r.get("when") or {})), None)
    if not matched:
        print("   · no rule matched → default sink: dashboard Activity tab only (NOT pushed)")
        return True

    print(f"   · rule matched: {matched.get('name')}")
    text = render_template(matched.get("template", "{message}"), event, defaults)
    actions = matched.get("card_actions")
    agent_name = event.get("agent_name") or defaults.get("agent_name", "agent")
    card = build_card(text, actions, agent_name, event, defaults)

    all_ok = True
    for dest_id in matched.get("push_to", []):
        dest = destinations.get(dest_id)
        if not dest:
            sys.stderr.write(f"   ! destination '{dest_id}' not declared in event-routing.yaml\n")
            all_ok = False
            continue
        if dest.get("via_connector") != "im-feishu":
            print(f"   · {dest_id} via {dest.get('via_connector')} — v0.1 only supports im-feishu, skipping")
            continue

        bot = (credentials or {}).get("bot_app") or {}
        chat_id = bot.get("notify_chat_id")
        if not chat_id:
            if dry:
                print("   · bot_app.notify_chat_id absent → using <PLACEHOLDER_CHAT_ID> for dry preview")
                chat_id = "<PLACEHOLDER_CHAT_ID>"
            else:
                sys.stderr.write(
                    f"   ! bot_app.notify_chat_id missing in credentials/feishu.yaml\n"
                    f"     → see docs/feishu-im-setup.md (Step 8-9)\n"
                )
                all_ok = False
                continue

        profile = bot.get("app_id") or "<APP_ID>"
        print(f"   → {dest_id}  chat_id={chat_id[:24]}…  profile={profile}")
        ok = send_to_feishu(chat_id, card, profile, dry)
        all_ok = all_ok and ok

    return all_ok


def main():
    p = argparse.ArgumentParser(prog="commando-route")
    p.add_argument("--agent-dir", default="./my-agent")
    p.add_argument("--event-file", default=None,
                   help="JSON file with a single event to route")
    p.add_argument("--demo", choices=list(DEMO_EVENTS.keys()), default=None,
                   help="Use one of the built-in demo events")
    p.add_argument("--apply", action="store_true",
                   help="Actually call lark-cli (default: dry-run)")
    p.add_argument("--credentials", default=None,
                   help="Override path to credentials yaml (default: <agent-dir>/credentials/feishu.yaml)")
    args = p.parse_args()

    if not args.demo and not args.event_file:
        sys.stderr.write("error: pass --demo <im|waiting|done|morning> or --event-file <path>\n")
        sys.exit(2)

    agent_dir = Path(args.agent_dir).resolve()
    if args.demo:
        event = dict(DEMO_EVENTS[args.demo])
        event["ts"] = datetime.now().isoformat()
        print(f"\n   event: built-in demo '{args.demo}'")
    else:
        event = json.loads(Path(args.event_file).read_text(encoding="utf-8"))
        print(f"\n   event: {event.get('event_id', '<no id>')}")

    routing = load_yaml(agent_dir / "event-routing.yaml")
    if not routing:
        sys.stderr.write(f"error: event-routing.yaml not found at {agent_dir}\n")
        sys.exit(2)

    cred_path = Path(args.credentials) if args.credentials else (agent_dir / "credentials" / "feishu.yaml")
    credentials = load_yaml(cred_path)
    if not credentials and args.apply:
        sys.stderr.write(f"error: credentials yaml not found at {cred_path}\n")
        sys.stderr.write(f"       run setup: docs/feishu-im-setup.md\n")
        sys.exit(2)

    dry = not args.apply
    print(f"   mode: {'DRY-RUN  (pass --apply to actually send)' if dry else 'APPLY  (will call lark-cli)'}\n")

    ok = route_event(event, routing, credentials, dry)
    print("")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

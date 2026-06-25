"""LLM client — uses whatever agent CLI the user already has installed.

commando is the Configuration layer. The LLM is **the user's choice**, not
something commando bundles. This module discovers an agent CLI in PATH and
shells out to it. No SDK is the "default".

Detection order (first found wins, override with $COMMANDO_LLM):
    claude   — Anthropic Claude Code           (verified)
    codex    — OpenAI Codex CLI                (community)
    kimi     — Moonshot Kimi CLI               (community)
    glm      — Zhipu GLM CLI                   (community)
    qwen     — Alibaba Qwen CLI                (community)
    doubao   — ByteDance Doubao CLI            (community)
    minimax  — MiniMax CLI                     (community)
    gemini   — Google Gemini CLI               (community)

For **headless cron** use where no interactive CLI is logged in, set
ANTHROPIC_API_KEY (env or credentials/anthropic.yaml) and we fall back to
the Anthropic SDK. SDK is **not the default** — it's a last resort for
unattended jobs.

To add a new CLI: open a PR adding an entry to AGENT_CLIS below. The
contract is `make_cmd(system, user, model) -> list[str]` returning argv.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Agent CLI registry — community-extensible
# ──────────────────────────────────────────────────────────────────────────────

def _claude_cmd(system: str, user: str, model: str) -> list:
    return [
        "claude", "-p", user,
        "--append-system-prompt", system,
        "--model", model,
    ]


def _codex_cmd(system: str, user: str, model: str) -> list:
    # Approximate; community to verify and PR fix
    return ["codex", "exec", user, "--model", model]


def _kimi_cmd(system: str, user: str, model: str) -> list:
    return ["kimi", "chat", "--system", system, user, "--model", model]


def _glm_cmd(system: str, user: str, model: str) -> list:
    return ["glm", "chat", "--system", system, user, "--model", model]


def _qwen_cmd(system: str, user: str, model: str) -> list:
    return ["qwen", "chat", "--system", system, user, "--model", model]


def _doubao_cmd(system: str, user: str, model: str) -> list:
    return ["doubao", "chat", "--system", system, user, "--model", model]


def _minimax_cmd(system: str, user: str, model: str) -> list:
    return ["minimax", "chat", "--system", system, user, "--model", model]


def _gemini_cmd(system: str, user: str, model: str) -> list:
    return ["gemini", "-p", user, "--system", system, "--model", model]


AGENT_CLIS: Dict[str, dict] = {
    "claude":  {"binary": "claude",  "make_cmd": _claude_cmd,  "verified": True},
    "codex":   {"binary": "codex",   "make_cmd": _codex_cmd,   "verified": False},
    "kimi":    {"binary": "kimi",    "make_cmd": _kimi_cmd,    "verified": False},
    "glm":     {"binary": "glm",     "make_cmd": _glm_cmd,     "verified": False},
    "qwen":    {"binary": "qwen",    "make_cmd": _qwen_cmd,    "verified": False},
    "doubao":  {"binary": "doubao",  "make_cmd": _doubao_cmd,  "verified": False},
    "minimax": {"binary": "minimax", "make_cmd": _minimax_cmd, "verified": False},
    "gemini":  {"binary": "gemini",  "make_cmd": _gemini_cmd,  "verified": False},
}

DETECTION_ORDER = ["claude", "codex", "kimi", "glm", "qwen", "doubao", "minimax", "gemini"]


# ──────────────────────────────────────────────────────────────────────────────
# Backend selection
# ──────────────────────────────────────────────────────────────────────────────

def _detect_cli() -> Optional[str]:
    """Honor $COMMANDO_LLM if set; otherwise return the first installed CLI in
    DETECTION_ORDER."""
    forced = os.environ.get("COMMANDO_LLM")
    if forced:
        if forced not in AGENT_CLIS:
            raise RuntimeError(
                f"$COMMANDO_LLM={forced} but commando doesn't know this CLI yet. "
                f"Known: {', '.join(AGENT_CLIS)}. PRs welcome to add it."
            )
        return forced
    for name in DETECTION_ORDER:
        if shutil.which(AGENT_CLIS[name]["binary"]):
            return name
    return None


def _load_anthropic_key(agent_dir: Path) -> Optional[str]:
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key
    cred = agent_dir / "credentials" / "anthropic.yaml"
    if cred.exists():
        try:
            import yaml  # type: ignore
            return (yaml.safe_load(cred.read_text(encoding="utf-8")) or {}).get("api_key")
        except Exception:
            return None
    return None


def _load_zhipu_key(agent_dir: Path) -> Optional[str]:
    """ZhipuAI (智谱) API key — checked from env or credentials/zhipu.yaml.
    Round 3 dogfood used GLM in Windsurf via the print-prompts path; this
    SDK fallback is for headless cron with the same provider."""
    env_key = os.environ.get("ZHIPU_API_KEY") or os.environ.get("ZHIPUAI_API_KEY")
    if env_key:
        return env_key
    cred = agent_dir / "credentials" / "zhipu.yaml"
    if cred.exists():
        try:
            import yaml  # type: ignore
            return (yaml.safe_load(cred.read_text(encoding="utf-8")) or {}).get("api_key")
        except Exception:
            return None
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Backend invocations
# ──────────────────────────────────────────────────────────────────────────────

def _call_via_cli(cli_name: str, system: str, user: str, model: str) -> dict:
    spec = AGENT_CLIS[cli_name]
    cmd = spec["make_cmd"](system, user, model)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{cli_name} CLI timed out after 180s")

    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        if not spec["verified"]:
            raise RuntimeError(
                f"{cli_name} CLI failed (rc={r.returncode}): {err[:300]}\n"
                f"Note: {cli_name} integration is community-stubbed. If the flag\n"
                f"      structure differs in your version, please PR commando/runtime/llm.py."
            )
        # claude / verified CLI failed — most common cause is auth not in subprocess
        is_auth = any(s in err.lower() for s in ("403", "forbidden", "unauthorized", "auth"))
        hint = ""
        if is_auth:
            hint = (
                "\n\n  This looks like a subprocess auth failure — your interactive\n"
                "  CLI auth doesn't propagate to subprocesses. Three fixes:\n"
                "\n"
                "    1) Best for IDE users (Cascade / Cursor / Claude Code):\n"
                "         commando build-skills --print-prompts\n"
                "       Print a self-contained prompt your IDE agent can run itself,\n"
                "       no subprocess, no API key.\n"
                "\n"
                "    2) Headless mode — set an API key for the subprocess:\n"
                "         export ANTHROPIC_API_KEY=sk-ant-…\n"
                "       (or write to credentials/anthropic.yaml)\n"
                "\n"
                "    3) Try a different backend:\n"
                "         export COMMANDO_LLM=codex   # or kimi / glm / qwen / …"
            )
        raise RuntimeError(f"{cli_name} CLI failed (rc={r.returncode}): {err[:400]}{hint}")

    return {
        "backend": f"{cli_name}-cli",
        "response_text": r.stdout.strip(),
        "model": f"{model} (via {cli_name} CLI)",
        "input_tokens": 0,    # CLI mode doesn't expose token counts
        "output_tokens": 0,
        "stop_reason": "end_turn",
    }


def _call_via_zhipu_sdk(api_key: str, system: str, user: str, model: str,
                        max_tokens: int) -> dict:
    """ZhipuAI Python SDK. Install: pip install zhipuai
    Round 3 dogfood validated GLM as agent backend via Windsurf print-prompts;
    this SDK path is the equivalent for headless cron."""
    try:
        from zhipuai import ZhipuAI  # type: ignore
    except ImportError:
        raise RuntimeError("zhipuai SDK not installed. Run: pip install zhipuai")
    client = ZhipuAI(api_key=api_key)
    # GLM uses an OpenAI-compatible chat.completions API.
    glm_model = model if model.startswith("glm-") else "glm-4-plus"
    resp = client.chat.completions.create(
        model=glm_model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    msg = resp.choices[0].message
    return {
        "backend": "zhipu-sdk",
        "response_text": msg.content or "",
        "model": glm_model,
        "input_tokens": getattr(resp.usage, "prompt_tokens", 0) if resp.usage else 0,
        "output_tokens": getattr(resp.usage, "completion_tokens", 0) if resp.usage else 0,
        "stop_reason": resp.choices[0].finish_reason or "stop",
    }


def _call_via_anthropic_sdk(api_key: str, system: str, user: str, model: str,
                            max_tokens: int) -> dict:
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        raise RuntimeError("anthropic SDK not installed. Run: pip install anthropic")
    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    response_text = msg.content[0].text if msg.content else ""
    return {
        "backend": "anthropic-sdk",
        "response_text": response_text,
        "model": msg.model,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
        "stop_reason": msg.stop_reason,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public entry
# ──────────────────────────────────────────────────────────────────────────────

def call_skill(
    *,
    agent_dir: Path,
    system_prompt: str,
    user_message: str,
    model: str = "claude-opus-4-7",
    max_tokens: int = 2048,
) -> dict:
    """Resolution order:
        1. Agent CLI in PATH (claude / codex / kimi / glm / qwen) — user's choice
        2. Anthropic SDK fallback for headless cron when ANTHROPIC_API_KEY set
        3. Fail with clear instructions
    """
    cli = _detect_cli()
    if cli:
        return _call_via_cli(cli, system_prompt, user_message, model)

    # No CLI found → try API-key fallbacks for headless cron, in priority order
    api_key = _load_anthropic_key(agent_dir)
    if api_key:
        return _call_via_anthropic_sdk(api_key, system_prompt, user_message, model, max_tokens)

    zhipu_key = _load_zhipu_key(agent_dir)
    if zhipu_key:
        return _call_via_zhipu_sdk(zhipu_key, system_prompt, user_message, model, max_tokens)

    raise RuntimeError(
        "no LLM backend available.\n"
        "  · Easiest (works in any IDE — verified Round 3 with GLM in Windsurf):\n"
        "       commando build-skills --print-prompts\n"
        "       (lets your IDE agent author Skill bodies — no API key needed)\n"
        "  · For headless cron use (no interactive login):\n"
        "       export ANTHROPIC_API_KEY=sk-ant-…    (or credentials/anthropic.yaml)\n"
        "       export ZHIPU_API_KEY=…               (or credentials/zhipu.yaml — for GLM)\n"
        "  · Or install an agent CLI:\n"
        "       Claude Code:  https://docs.claude.com/en/docs/claude-code\n"
        "       OpenAI Codex: https://github.com/openai/codex\n"
        "       Kimi / GLM / Qwen / Doubao / MiniMax CLIs: see their respective docs"
    )

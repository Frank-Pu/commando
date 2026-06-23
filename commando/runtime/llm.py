"""LLM client — single-shot Skill execution with auto-fallback.

Backend resolution order:
  1. ANTHROPIC_API_KEY env var or credentials/anthropic.yaml → Anthropic SDK
     (best for headless / cron — independent of Claude Code login state)
  2. `claude` CLI in PATH                                    → claude -p subprocess
     (best for users who already have Claude Code — zero extra config)
  3. otherwise                                               → fail with clear instructions
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _load_api_key(agent_dir: Path) -> Optional[str]:
    """Read ANTHROPIC_API_KEY env var first; fall back to credentials/anthropic.yaml."""
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key

    cred_path = agent_dir / "credentials" / "anthropic.yaml"
    if cred_path.exists():
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(cred_path.read_text(encoding="utf-8")) or {}
            return data.get("api_key")
        except Exception:
            return None

    return None


def _call_via_sdk(api_key: str, system_prompt: str, user_message: str,
                  model: str, max_tokens: int) -> dict:
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        raise RuntimeError("anthropic SDK not installed. Run: pip install anthropic")

    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
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


def _call_via_claude_cli(system_prompt: str, user_message: str, model: str) -> dict:
    if shutil.which("claude") is None:
        raise RuntimeError("`claude` CLI not in PATH")

    cmd = [
        "claude", "-p", user_message,
        "--append-system-prompt", system_prompt,
        "--model", model,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise RuntimeError("claude CLI timed out after 120s")

    if r.returncode != 0:
        raise RuntimeError(f"claude CLI failed (rc={r.returncode}): {(r.stderr or r.stdout).strip()[:400]}")

    return {
        "backend": "claude-cli",
        "response_text": r.stdout.strip(),
        "model": f"{model} (via claude CLI)",
        # claude CLI does not expose token counts in --print mode
        "input_tokens": 0,
        "output_tokens": 0,
        "stop_reason": "end_turn",
    }


def call_skill(
    *,
    agent_dir: Path,
    system_prompt: str,
    user_message: str,
    model: str = "claude-opus-4-7",
    max_tokens: int = 2048,
) -> dict:
    """Try Anthropic SDK first; fall back to `claude` CLI if available."""
    api_key = _load_api_key(agent_dir)
    if api_key:
        return _call_via_sdk(api_key, system_prompt, user_message, model, max_tokens)

    if shutil.which("claude"):
        return _call_via_claude_cli(system_prompt, user_message, model)

    raise RuntimeError(
        "no LLM backend available. Either:\n"
        "  1. export ANTHROPIC_API_KEY=sk-ant-…   (or write to credentials/anthropic.yaml)\n"
        "  2. install Claude Code:  https://docs.claude.com/en/docs/claude-code/getting-started"
    )

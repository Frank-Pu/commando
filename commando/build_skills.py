"""commando build-skills — turn draft skills into runnable ones.

The bridge between "Onboarding decided WHAT skills you need" (metadata stubs)
and "Runtime can actually execute them" (real prompt bodies).

After Onboarding finishes, skills are status: draft — they have frontmatter
and I/O contracts but NO prompt body. Without a body the LLM has nothing to
follow when `commando run --task X` fires. This command calls your AI tool
once per draft skill to write the body, using:
    · charter.md           (the agent's persona / voice / red lines)
    · skill metadata       (name / description / I/O contract / capabilities)
    · playbook context     (general patterns for this role family)
"""

import sys
from pathlib import Path
from typing import Tuple

import click


META_PROMPT_TEMPLATE = """You are commando's Skill Authoring assistant.

A draft skill needs its body written. You have:
  · the agent's Charter (the agent's constitution — voice, ICP, red lines)
  · the skill's metadata (frontmatter + intro scaffolded by Onboarding)
  · optional playbook context (general patterns for the role)

Your job: write the SKILL.md BODY ONLY (no frontmatter, no commentary, no
``` fences). The body is the actual prompt the agent will follow when this
skill fires at runtime.

═══════════════════════════════════════════════════════════════
TWO HARD RULES BEFORE YOU WRITE A WORD
═══════════════════════════════════════════════════════════════

**Rule 1 — Only write what AI doesn't already know.**

The runtime LLM has broad general knowledge. Telling it "write a clear
post" or "analyze carefully" or "ensure high quality" is **wasted tokens**
— it already tries to do that. The Skill's *only* value is the
**incremental, agent-specific information** you encode:
  · which Charter section to apply (cite by §)
  · which playbook formula/framework to use (cite by name)
  · which ICP and red lines from this agent's Charter constrain output
  · which inputs feed this skill at runtime
  · which output format is structured (table columns, JSON schema, etc.)

If a sentence in your output could appear unchanged in ANY agent's skill,
delete it. Replace with a sentence that only makes sense for THIS agent.

  ✗ BAD:  "Analyze the input carefully. Write a high-quality post."
  ✓ GOOD: "Score input against Charter §2.2 ICP (偏女生偏备考的中国大学生).
           If ICP-fit < 3/5, drop. Otherwise apply Charter §4.2 Bridge
           formula (50/30/20 = 痛点/解法/CTA)."

**Rule 2 — Skills must work standalone. Connectors are enhancement only.**

NEVER make the skill's main process depend on a specific tool name (飞书,
Notion, Slack). If the skill needs to "send a notification", the main
Process step says "deliver to user IM" — and the optional "If Connectors
Available" section at the END names tool categories.

  ✗ BAD:  "Step 5: Use Feishu MCP to post the card to chat_id ou_xxx."
  ✓ GOOD: "Step 5: Output the card payload to ./workbench/ as YAML;
          if **IM 推送** is connected, the card auto-routes there."

═══════════════════════════════════════════════════════════════
AGENT CHARTER
═══════════════════════════════════════════════════════════════
{charter}

═══════════════════════════════════════════════════════════════
DRAFT SKILL (frontmatter + Onboarding-scaffolded intro)
═══════════════════════════════════════════════════════════════
{skill_metadata}

═══════════════════════════════════════════════════════════════
PLAYBOOK CONTEXT
═══════════════════════════════════════════════════════════════
{playbook}

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT (strict — exactly 6 sections, in this order)
═══════════════════════════════════════════════════════════════
Write the body as markdown. Start with this exact line:

    # /{skill_name} — <one-sentence description in user's actual words>

Then write the runtime prompt. Six required sections:

1. **Identity anchor** (1-2 lines):
   "You ARE the agent described in the Charter injected at the top of
    this context. Voice + red lines apply — see Charter §<voice section>
    and §<red lines section>."

2. **Inputs** (a bulleted list):
   Exactly what the agent receives at runtime. Pull from schedule.yaml
   `inputs:` block + memory layers (Working / Episodic / Semantic) +
   connector data sources. Be concrete: "上周 KPI table 第 N 行" not
   "the data".

3. **Process** (3-7 numbered steps):
   Concrete actions. For EACH step that involves judgment, cite the
   Charter section or playbook framework that governs the judgment.
   Use **conditional branches** when input shape varies:
     "If <X> → path A; else if <Y> → path B; else fallback to C."
   Use **fallback logic** for incomplete inputs:
     "If <expected data> missing, note as gap in episodic event and
      proceed with reduced confidence label."

4. **Output** (concrete):
   Exactly what gets written where. If structured (workbench row /
   IM card / Semantic memory entry), give the column or field list.
   Reference the schedule.yaml `outputs:` block for routing.

5. **Voice / quality gates** (3-5 bullets):
   Reference Charter sections by §number. What makes output PASS vs FAIL
   for THIS agent specifically (not generic "be clear / be accurate"):
     · "AIGC 手改率 ≥ 20%（Charter §6 红线）"
     · "ICP 命中度 ≥ 4/5（Charter §2.2 ICP 校准）"
     · "营销密度 ≤ 20%（Charter §6 红线）"

6. **If Connectors Available** (FIXED section title, always at end):
   Use **connector category names** (IM 推送 / 文档协作 / 结构化记录 /
   信息源 / 网页抓取 / 数据库), NEVER specific tool names (飞书 / Notion).
   For each category that would enhance this skill, ONE line describing
   the user-visible upgrade:

       ## If Connectors Available

       If **IM 推送** is connected:
         - 完稿后自动推 IM 卡片，用户在飞书/钉钉/Slack 收到即审

       If **文档协作** is connected:
         - 终稿自动同步到协作平台，方便团队复用

       If no connectors available:
         - 输出到 ./workbench/ 本地文件，用户手动复制（默认行为）

   **The "If no connectors available" fallback is REQUIRED** — every
   Skill must work in isolation.

═══════════════════════════════════════════════════════════════
LENGTH + STYLE
═══════════════════════════════════════════════════════════════
  · 500-1500 words total
  · Concrete > abstract on every sentence
  · Reference Charter §<n> > generic encouragement
  · Use the user's actual words from Charter (产品名、ICP 标签、渠道名)
  · No `<placeholder>` strings in the final output — fill them in or
    drop the section

Do not output frontmatter. Do not output ``` fences. Do not preface with
"Here's the body". Output only the markdown body.
"""


# ──────────────────────────────────────────────────────────────────────────────
# SKILL.md parse + write
# ──────────────────────────────────────────────────────────────────────────────

def _read_skill(path: Path) -> Tuple[dict, str]:
    import yaml
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    try:
        fm = yaml.safe_load(text[4:end]) or {}
    except Exception:
        fm = {}
    return fm, text[end + 5:]


def _write_skill(path: Path, frontmatter: dict, body: str) -> None:
    import yaml
    fm_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n\n{body.lstrip()}\n", encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Playbook discovery
# ──────────────────────────────────────────────────────────────────────────────

def _find_playbook(agent_dir: Path) -> str:
    repo_root = Path(__file__).resolve().parent.parent
    playbooks_dir = repo_root / "playbooks"
    if not playbooks_dir.exists():
        return ""

    charter = agent_dir / "charter.md"
    if charter.exists():
        text = charter.read_text(encoding="utf-8", errors="ignore").lower()
        for pb_file in sorted(playbooks_dir.glob("*.md")):
            slug = pb_file.stem
            if slug.startswith("_"):
                continue
            if slug in text:
                return pb_file.read_text(encoding="utf-8")

    generic = playbooks_dir / "_generic.md"
    if generic.exists():
        return generic.read_text(encoding="utf-8")
    return ""


# ──────────────────────────────────────────────────────────────────────────────
# Build one skill
# ──────────────────────────────────────────────────────────────────────────────

def _build_one(agent_dir: Path, skill_path: Path, charter: str, playbook: str,
               force: bool, apply: bool) -> str:
    import yaml

    fm, body = _read_skill(skill_path)
    name = fm.get("name", skill_path.parent.name)
    status = fm.get("status", "draft")
    description = fm.get("description", "")

    if status == "active" and not force:
        click.secho(f"    ⊘ {name}  (already active, use --force to rebuild)", fg="bright_black")
        return "skipped-active"

    if status == "imported-placeholder":
        click.secho(f"    ⊘ {name}  (Registry-imported placeholder — run `commando install` instead)", fg="bright_black")
        return "skipped-imported"

    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    body_intro = "\n".join(body.split("\n")[:50])
    metadata = f"---\n{fm_yaml}---\n\n{body_intro}"

    user_msg = META_PROMPT_TEMPLATE.format(
        charter=charter,
        skill_metadata=metadata,
        playbook=playbook[:8000] if playbook else "(no playbook found — use Charter alone)",
        skill_name=name,
    )

    if not apply:
        click.echo(f"    [DRY] would build {name}  (description: {description[:60]})")
        click.secho(f"           prompt = {len(user_msg)} chars → LLM", fg="bright_black")
        return "would-build"

    click.echo(f"    → calling LLM for {name}…")
    from commando.runtime.llm import call_skill
    try:
        result = call_skill(
            agent_dir=agent_dir,
            system_prompt="You are a precise Skill authoring assistant for commando.",
            user_message=user_msg,
            model=fm.get("model") or "claude-opus-4-7",
            max_tokens=4096,
        )
    except Exception as e:
        click.secho(f"    ✗ {name}: LLM call failed: {str(e)[:200]}", fg="red")
        return "failed"

    new_body = result["response_text"].strip()
    # Strip any accidental ``` fences
    if new_body.startswith("```"):
        lines = new_body.split("\n")
        new_body = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    if len(new_body) < 300:
        click.secho(f"    ✗ {name}: LLM returned suspiciously short body ({len(new_body)} chars)", fg="red")
        return "failed"

    fm["status"] = "active"
    _write_skill(skill_path, fm, new_body)
    click.secho(f"    ✓ {name}  ({len(new_body)} chars, status → active)", fg="green")
    return "built"


# ──────────────────────────────────────────────────────────────────────────────
# Public entry
# ──────────────────────────────────────────────────────────────────────────────

def _print_host_agent_prompt(skill_files, charter: str, playbook: str,
                             agent_dir: Path, force: bool) -> int:
    """Print ONE self-contained meta-prompt the host agent (Cascade / Cursor /
    Claude Code / etc.) can paste-execute itself — no subprocess, no auth.

    Returns count of skills that would be built.
    """
    drafts = []
    for sp in skill_files:
        fm, _ = _read_skill(sp)
        status = fm.get("status", "draft")
        if status == "active" and not force:
            continue
        if status == "imported-placeholder":
            continue
        drafts.append((sp, fm))

    if not drafts:
        click.echo()
        click.secho("  Nothing to print — no draft skills.", fg="green")
        return 0

    click.echo()
    click.secho("  ─── COPY everything below this line into your AI agent ───", fg="cyan", bold=True)
    click.echo()
    click.echo("=" * 70)
    click.echo()
    click.echo(f"You're going to author the prompt body for {len(drafts)} draft Skill(s)")
    click.echo("in this commando agent. You already have full Onboarding context in")
    click.echo("this conversation, so this should be straightforward.")
    click.echo()
    click.echo("For EACH draft skill listed below:")
    click.echo("  1. Read the existing SKILL.md (note its frontmatter + intro)")
    click.echo("  2. Write a NEW prompt body following the rules in the META_GUIDE section")
    click.echo("  3. Use your file-write tool to overwrite SKILL.md with:")
    click.echo("       - the SAME frontmatter, BUT change `status: draft` → `status: active`")
    click.echo("       - your new prompt body below the frontmatter")
    click.echo()
    click.echo("=" * 70)
    click.echo()
    click.echo("META_GUIDE for writing each Skill body:")
    click.echo()
    click.echo(META_PROMPT_TEMPLATE.format(
        charter="<see CHARTER block below — apply it to every skill>",
        skill_metadata="<see PER_SKILL list below — one entry per skill>",
        playbook="<see PLAYBOOK block below — apply to every skill>",
        skill_name="<skill-name, from frontmatter>",
    ))
    click.echo()
    click.echo("=" * 70)
    click.echo()
    click.echo("CHARTER (the agent's constitution — same for all skills):")
    click.echo()
    click.echo(charter)
    click.echo()
    click.echo("=" * 70)
    click.echo()
    click.echo("PLAYBOOK (general patterns for this role family):")
    click.echo()
    click.echo(playbook[:8000] if playbook else "(no playbook found)")
    click.echo()
    click.echo("=" * 70)
    click.echo()
    click.echo(f"PER_SKILL list — write a body for each, then overwrite the SKILL.md:")
    click.echo()
    import yaml
    for sp, fm in drafts:
        click.echo("-" * 70)
        click.echo(f"  Skill name: {fm.get('name', sp.parent.name)}")
        click.echo(f"  Write to:   {sp}")
        click.echo(f"  Description: {fm.get('description', '(none)')}")
        click.echo(f"  Tags: {fm.get('tags', [])}")
        click.echo(f"  Capability requirements: {fm.get('capability_requirements', [])}")
        click.echo()
        body_intro = "\n".join((sp.read_text(encoding="utf-8").split("---\n", 2)[-1]).split("\n")[:20])
        click.echo(f"  Onboarding-scaffolded intro (extend, don't discard):")
        for line in body_intro.split("\n"):
            click.echo(f"    {line}")
        click.echo()
    click.echo("=" * 70)
    click.echo()
    click.echo(f"When done, run `commando status --agent-dir {agent_dir}` — it should")
    click.echo(f"show {len(drafts)} more active skill(s).")
    click.echo()
    click.secho("  ─── END copy region ───", fg="cyan", bold=True)
    click.echo()
    return len(drafts)


def run(target: str, skill_id: str = None, apply: bool = False, force: bool = False,
        print_prompts: bool = False) -> None:
    agent_dir = Path(target).resolve()

    click.echo()
    click.secho("  commando build-skills", fg="cyan", bold=True)
    click.secho("  " + "─" * 60, fg="bright_black")
    click.echo()
    click.echo(f"  agent dir : {agent_dir}")
    click.echo(f"  mode      : {'APPLY (calls LLM, rewrites SKILL.md)' if apply else 'DRY-RUN (use --apply for real)'}")

    charter_path = agent_dir / "charter.md"
    if not charter_path.exists():
        click.secho(f"\n  ✗ no charter.md at {charter_path}", fg="red")
        sys.exit(2)
    charter = charter_path.read_text(encoding="utf-8")

    playbook = _find_playbook(agent_dir)
    if playbook:
        click.echo(f"  playbook  : found ({len(playbook)} chars)")
    else:
        click.echo(f"  playbook  : (none found — using Charter alone)")

    skills_dir = agent_dir / "skills"
    if not skills_dir.exists():
        click.secho(f"\n  ✗ no skills/ at {skills_dir}", fg="red")
        sys.exit(2)

    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if skill_id:
        skill_files = [s for s in skill_files if s.parent.name == skill_id]
        if not skill_files:
            click.secho(f"\n  ✗ no skill matching id '{skill_id}'", fg="red")
            sys.exit(2)

    if not skill_files:
        click.echo("\n  No skills found in skills/.")
        return

    if print_prompts:
        n = _print_host_agent_prompt(skill_files, charter, playbook, agent_dir, force)
        return

    click.echo()
    click.echo(f"  Found {len(skill_files)} skill(s):")
    click.echo()

    results = {}
    for skill_path in skill_files:
        status = _build_one(agent_dir, skill_path, charter, playbook, force, apply)
        results[status] = results.get(status, 0) + 1

    click.echo()
    if apply:
        built = results.get("built", 0)
        failed = results.get("failed", 0)
        skipped = results.get("skipped-active", 0) + results.get("skipped-imported", 0)
        click.secho(f"  ✓ built: {built}  |  skipped: {skipped}  |  failed: {failed}", fg="green" if failed == 0 else "yellow")
        if built > 0:
            click.echo()
            click.echo("  These skills are now status: active and runnable. Try:")
            click.echo(f"    commando run --task <id> --apply")
    else:
        would = results.get("would-build", 0)
        click.echo(f"  Dry-run: would build {would} skill(s). Run with --apply for real.")
    click.echo()

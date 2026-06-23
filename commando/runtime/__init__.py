"""commando.runtime — minimal Runtime Core for v0.2.

v0.2 scope:
  - one-shot execution of a single task via `commando run --task <id>`
  - load Charter + Skill, call Anthropic API, write event to Episodic Memory
  - --dry default, --apply for real API call

Not in v0.2 (later):
  - cron-driven background loop
  - Workbench state machine
  - chain triggers
  - Eval system
"""

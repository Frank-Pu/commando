"""commando connectors — runtime drivers for external services.

Each connector lives in its own module here. Skills import the driver
directly when they need to read/write to a backend. The runtime is
deliberately thin: connectors are just functions, not a plugin system.

Built-in:
  · obsidian  — write markdown to a local Obsidian vault

Coming via community contribution (see docs/CONNECTORS-CONTRIBUTING.md):
  · notion    — Notion REST API or official MCP server
  · slack     — Slack incoming webhook or Web API
  · stripe    — Stripe CLI / REST API for finance agents
  · gmail     — Google Workspace API
"""

---
description: Inject minimum sphinx-needs configuration into an existing Sphinx project so sphinx-build produces a valid needs.json.
handoffs:
  - label: Detect and scaffold Pharaoh
    agent: pharaoh.setup
    prompt: Detect the freshly configured sphinx-needs project and scaffold pharaoh.toml
---

# @pharaoh.bootstrap

Inject the minimum sphinx-needs configuration — extension entry, need types, optional extra links — into an existing Sphinx project that does not yet have sphinx-needs configured. Does not seed RST content, does not build, does not write `pharaoh.toml`.

See [`skills/pharaoh-bootstrap/SKILL.md`](../../skills/pharaoh-bootstrap/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

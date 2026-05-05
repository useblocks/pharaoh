---
description: Use when a Sphinx project has no sphinx-needs configured and you need minimum viable scaffolding — adding the extension and declaring need types — so that sphinx-build produces a valid needs.json for downstream Pharaoh skills.
handoffs:
  - label: Detect and scaffold Pharaoh
    agent: pharaoh.setup
    prompt: Detect the freshly configured sphinx-needs project and scaffold pharaoh.toml
---

# @pharaoh.bootstrap

Use when a Sphinx project has no sphinx-needs configured and you need minimum viable scaffolding — adding the extension and declaring need types — so that sphinx-build produces a valid needs.json for downstream Pharaoh skills.

See [`skills/pharaoh-bootstrap/SKILL.md`](../../skills/pharaoh-bootstrap/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

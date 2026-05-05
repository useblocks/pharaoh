---
description: Use when about to dispatch a fan-out of emission subagents (pharaoh-req-from-code, pharaoh-feat-draft-from-docs) and you need to pre-allocate globally-unique sphinx-needs IDs. Each subagent receives its pre-allocated pool and emits only from that pool, so parallel agents cannot collide on stem choice. Does NOT invoke emitters, does NOT write RST.
handoffs: []
---

# @pharaoh.id-allocate

Use when about to dispatch a fan-out of emission subagents (pharaoh-req-from-code, pharaoh-feat-draft-from-docs) and you need to pre-allocate globally-unique sphinx-needs IDs. Each subagent receives its pre-allocated pool and emits only from that pool, so parallel agents cannot collide on stem choice. Does NOT invoke emitters, does NOT write RST.

See [`skills/pharaoh-id-allocate/SKILL.md`](../../skills/pharaoh-id-allocate/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

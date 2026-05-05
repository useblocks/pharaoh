---
description: Use when authoring or modifying a single sphinx-needs artefact (requirement, architecture element, test case, decision) by routing to the matching atomic drafting skill based on the project's artefact catalog. Returns the drafted RST directive with an ID, file placement suggestion, and parent link.
handoffs:
  - label: Verify Authored Need
    agent: pharaoh.verify
    prompt: Check that the authored artefact addresses the substance of its parent
  - label: Review Drafted Requirement
    agent: pharaoh.req-review
    prompt: Audit the drafted requirement against the ISO 26262 §6 axes
  - label: Trace the Authored Need
    agent: pharaoh.trace
    prompt: Trace the new artefact through all link types
---

# @pharaoh.author

Use when authoring or modifying a single sphinx-needs artefact (requirement, architecture element, test case, decision) by routing to the matching atomic drafting skill based on the project's artefact catalog. Returns the drafted RST directive with an ID, file placement suggestion, and parent link.

See [`skills/pharaoh-author/SKILL.md`](../../skills/pharaoh-author/SKILL.md) for the full atomic specification — inputs, dispatch table, and composition patterns.

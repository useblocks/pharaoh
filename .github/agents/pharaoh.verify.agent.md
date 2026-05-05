---
description: Use when checking whether one sphinx-needs artefact actually addresses the substance of every parent it links to via :satisfies: or :verifies:. Cross-need content check — distinct from structural MECE, schema-level tailor-review, and per-axis req-review/arch-review.
handoffs:
  - label: MECE Check
    agent: pharaoh.mece
    prompt: Run a structural gap-and-orphan analysis around the verified need
  - label: Trace the Need
    agent: pharaoh.trace
    prompt: Trace the verified need through every link type
  - label: Re-author the Need
    agent: pharaoh.author
    prompt: Revise the body to address the missing parent claims
---

# @pharaoh.verify

Use when checking whether one sphinx-needs artefact actually addresses the substance of every parent it links to via :satisfies: or :verifies:. Cross-need content check — distinct from structural MECE, schema-level tailor-review, and per-axis req-review/arch-review.

See [`skills/pharaoh-verify/SKILL.md`](../../skills/pharaoh-verify/SKILL.md) for the full atomic specification — inputs, scoring scale, and composition patterns.

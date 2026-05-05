---
description: Use when drafting a single sphinx-needs architecture element from one parent requirement. The artefact type is parameterised via `target_level` (any catalog-declared architecture type — e.g. `arch`, `swarch`, `sys-arch`, `module`, `component`, `interface`). Emits an RST directive block linking back to the parent via `:satisfies:`.
handoffs: []
---

# @pharaoh.arch-draft

Use when drafting a single sphinx-needs architecture element from one parent requirement. The artefact type is parameterised via `target_level` (any catalog-declared architecture type — e.g. `arch`, `swarch`, `sys-arch`, `module`, `component`, `interface`). Emits an RST directive block linking back to the parent via `:satisfies:`.

See [`skills/pharaoh-arch-draft/SKILL.md`](../../skills/pharaoh-arch-draft/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

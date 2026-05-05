---
description: Use when drafting a single sphinx-needs test-case (verification plan item) for one requirement. The artefact type is parameterised via `target_level` (any catalog-declared verification-plan / test-case type — e.g. `tc`, `test`, `vplan`). Emits an RST directive with inputs, steps, and expected outcome, linking to the parent req via `:verifies:`.
handoffs: []
---

# @pharaoh.vplan-draft

Use when drafting a single sphinx-needs test-case (verification plan item) for one requirement. The artefact type is parameterised via `target_level` (any catalog-declared verification-plan / test-case type — e.g. `tc`, `test`, `vplan`). Emits an RST directive with inputs, steps, and expected outcome, linking to the parent req via `:verifies:`.

See [`skills/pharaoh-vplan-draft/SKILL.md`](../../skills/pharaoh-vplan-draft/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

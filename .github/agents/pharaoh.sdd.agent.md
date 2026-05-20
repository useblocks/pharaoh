---
description: Use when a developer wants to add a feature, capability, or behaviour change to a project that uses sphinx-needs and a V-model artefact structure, before any requirement or code is written. Triggers on "add a feature", "implement X", "let's build Y", or "do spec-driven development" in a project with `.pharaoh/project/` tailoring. Non-atomic orchestrator: elicits requirements from the developer (Phase 0), then walks the V-model tiers one at a time, dispatching atomic draft and review skills, running `sphinx-build -W` after each tier, and waiting for human approval before advancing. Ends with a `pharaoh-quality-gate` pass confirming review coverage and trace completeness.
handoffs: []
---

# @pharaoh.sdd

Use when a developer wants to add a feature, capability, or behaviour change to a project that uses sphinx-needs and a V-model artefact structure, before any requirement or code is written. Triggers on "add a feature", "implement X", "let's build Y", or "do spec-driven development" in a project with `.pharaoh/project/` tailoring.

Non-atomic orchestrator: elicits requirements from the developer (Phase 0), then walks the V-model tiers one at a time, dispatching atomic draft and review skills, running `sphinx-build -W` after each tier, and waiting for human approval before advancing. Ends with a `pharaoh-quality-gate` pass confirming review coverage and trace completeness.

See [`skills/pharaoh-sdd/SKILL.md`](../../skills/pharaoh-sdd/SKILL.md) for the full specification -- inputs, outputs, the iron gate contract, and the tier loop detail.

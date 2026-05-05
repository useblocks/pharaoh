---
description: Use when authoring a project's `code-grounding-filters.yaml` from observed stack conventions. Detects language + CLI framework + config-object style in the project source tree and emits a tailoring YAML populated with the four parameterised filter strategies. Does not invoke `pharaoh-req-code-grounding-check`; purely produces tailoring.
handoffs: []
---

# @pharaoh.tailor-code-grounding-filters

Use when authoring a project's `code-grounding-filters.yaml` from observed stack conventions. Detects language + CLI framework + config-object style in the project source tree and emits a tailoring YAML populated with the four parameterised filter strategies. Does not invoke `pharaoh-req-code-grounding-check`; purely produces tailoring.

See [`skills/pharaoh-tailor-code-grounding-filters/SKILL.md`](../../skills/pharaoh-tailor-code-grounding-filters/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

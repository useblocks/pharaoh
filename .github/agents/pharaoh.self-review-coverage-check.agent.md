---
description: Use when verifying that every artefact emitted during a plan run received a matching review. For every drafted artefact in `runs/`, confirms a matching `<id>_review.json` exists and is non-empty. Closes the "draft emitted but review was skipped" failure class.
handoffs: []
---

# @pharaoh.self-review-coverage-check

Use when verifying that every artefact emitted during a plan run received a matching review. For every drafted artefact in `runs/`, confirms a matching `<id>_review.json` exists and is non-empty. Closes the "draft emitted but review was skipped" failure class.

See [`skills/pharaoh-self-review-coverage-check/SKILL.md`](../../skills/pharaoh-self-review-coverage-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

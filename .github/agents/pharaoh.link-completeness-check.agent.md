---
description: Use when verifying outgoing-link coverage across a full needs.json graph. For each declared link type in `artefact-catalog.yaml`, confirms every need of the governed type carries a non-empty value AND every target id resolves to an existing need. Closes the "catalogue declares `verifies` required but half the reqs ship without it" failure class.
handoffs: []
---

# @pharaoh.link-completeness-check

Use when verifying outgoing-link coverage across a full needs.json graph. For each declared link type in `artefact-catalog.yaml`, confirms every need of the governed type carries a non-empty value AND every target id resolves to an existing need. Closes the "catalogue declares `verifies` required but half the reqs ship without it" failure class.

See [`skills/pharaoh-link-completeness-check/SKILL.md`](../../skills/pharaoh-link-completeness-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

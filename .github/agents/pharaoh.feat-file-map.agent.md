---
description: Use when mapping one feature (already emitted as an RST directive) to the source files that implement it. Reads the source tree, returns a YAML entry `{feat_id: {files: [...], rationale: "..."}}`. Does NOT read docs. Does NOT emit reqs. Does NOT create or modify source files.
handoffs: []
---

# @pharaoh.feat-file-map

Use when mapping one feature (already emitted as an RST directive) to the source files that implement it. Reads the source tree, returns a YAML entry `{feat_id: {files: [...], rationale: "..."}}`. Does NOT read docs. Does NOT emit reqs. Does NOT create or modify source files.

See [`skills/pharaoh-feat-file-map/SKILL.md`](../../skills/pharaoh-feat-file-map/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

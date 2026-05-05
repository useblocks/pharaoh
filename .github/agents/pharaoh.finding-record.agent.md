---
description: Use when recording an audit finding in the shared Papyrus workspace with automatic dedup. Uses deterministic ID to ensure the same {category, subject_id} tuple never appears twice across concurrent subagents. Returns {action: wrote|duplicate, papyrus_id}.
handoffs: []
---

# @pharaoh.finding-record

Use when recording an audit finding in the shared Papyrus workspace with automatic dedup. Uses deterministic ID to ensure the same {category, subject_id} tuple never appears twice across concurrent subagents. Returns {action: wrote|duplicate, papyrus_id}.

See [`skills/pharaoh-finding-record/SKILL.md`](../../skills/pharaoh-finding-record/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

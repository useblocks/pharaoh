---
description: Use when running a full project audit in parallel by dispatching 5 atomic audit skills, each writing findings to a shared Papyrus workspace via pharaoh-finding-record for automatic deduplication. Emits the aggregated deduplicated findings list.
handoffs: []
---

# @pharaoh.audit-fanout

Use when running a full project audit in parallel by dispatching 5 atomic audit skills, each writing findings to a shared Papyrus workspace via pharaoh-finding-record for automatic deduplication. Emits the aggregated deduplicated findings list.

See [`skills/pharaoh-audit-fanout/SKILL.md`](../../skills/pharaoh-audit-fanout/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

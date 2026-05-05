---
description: Use when a reverse-engineering run (a plan emitted by pharaoh-write-plan) finds pre-existing prose documentation files in the target output directory that would collide with generated feat RST files. Produces a sentence-by-sentence migration proposal — keep-as-user-guide, merge-into-feat-body, discard. Does NOT overwrite anything; the caller applies the proposal manually.
handoffs: []
---

# @pharaoh.prose-migrate

Use when a reverse-engineering run (a plan emitted by pharaoh-write-plan) finds pre-existing prose documentation files in the target output directory that would collide with generated feat RST files. Produces a sentence-by-sentence migration proposal — keep-as-user-guide, merge-into-feat-body, discard. Does NOT overwrite anything; the caller applies the proposal manually.

See [`skills/pharaoh-prose-migrate/SKILL.md`](../../skills/pharaoh-prose-migrate/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

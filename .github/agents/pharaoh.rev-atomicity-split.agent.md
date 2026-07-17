---
description: Use when a recovered need bundles several atomic requirements and must be split into atomic needs without losing its links. Detects a conjunction or more than one `shall` inside a single recovered need's body, re-emits one atomic need per behavior, and carries the original need's up-links onto every atom unchanged. Leaves an already-atomic need untouched. Does NOT synthesize a new higher-rung need (that is `pharaoh-rev-cluster-synthesize`) and does NOT invoke the CLI (that is `pharaoh-rev-record-ledger`).
handoffs: []
---

# @pharaoh.rev-atomicity-split

Use when a recovered need bundles several atomic requirements and must be split into atomic needs without losing its links. Detects a conjunction or more than one `shall` inside a single recovered need's body, re-emits one atomic need per behavior, and carries the original need's up-links onto every atom unchanged. Leaves an already-atomic need untouched. Does NOT synthesize a new higher-rung need (that is `pharaoh-rev-cluster-synthesize`) and does NOT invoke the CLI (that is `pharaoh-rev-record-ledger`).

See [`skills/pharaoh-rev-atomicity-split/SKILL.md`](../../skills/pharaoh-rev-atomicity-split/SKILL.md) for the full atomic specification -- inputs, outputs, atomicity contract, and composition patterns.

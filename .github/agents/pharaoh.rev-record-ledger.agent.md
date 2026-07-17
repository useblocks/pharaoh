---
description: Use when a recovery emission from `pharaoh-req-from-code`, `pharaoh-rev-cluster-synthesize`, or `pharaoh-rev-atomicity-split` is ready to persist into the project's needs corpus. Wraps the emission into the engine's `RecoveryResult` shape, applies any pending cluster member up-links, writes it to a temp file, and runs `ubc agent reverse record --input <tempfile>` -- the only skill in the tree allowed to shell out to that command. Returns the CLI's JSON stdout unchanged.
handoffs: []
---

# @pharaoh.rev-record-ledger

Use when a recovery emission from `pharaoh-req-from-code`, `pharaoh-rev-cluster-synthesize`, or `pharaoh-rev-atomicity-split` is ready to persist into the project's needs corpus. Wraps the emission into the engine's `RecoveryResult` shape, applies any pending cluster member up-links, writes it to a temp file, and runs `ubc agent reverse record --input <tempfile>` -- the only skill in the tree allowed to shell out to that command. Returns the CLI's JSON stdout unchanged.

See [`skills/pharaoh-rev-record-ledger/SKILL.md`](../../skills/pharaoh-rev-record-ledger/SKILL.md) for the full atomic specification -- inputs, outputs, atomicity contract, and composition patterns.

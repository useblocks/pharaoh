---
description: Use when a recovery emission from `pharaoh-req-from-code`, `pharaoh-rev-cluster-synthesize`, or `pharaoh-rev-atomicity-split` is ready to persist into the project's advisory ledger. Wraps the emission into the engine's `RecoveryResult` shape (`reqs` -> `needs`, matching `RecoveredNeed`), writes it to a temp file, and runs `ubc agent reverse record --input <tempfile>` -- the only skill in the tree allowed to shell out to that command. `record` is the ledger's only writer and never touches RST. It does not apply cluster member up-links -- those are authored directly into RST by `pharaoh-rev-cluster-synthesize` (see that skill's `member_updates` output). Returns the CLI's JSON stdout unchanged.
handoffs: []
---

# @pharaoh.rev-record-ledger

Use when a recovery emission from `pharaoh-req-from-code`, `pharaoh-rev-cluster-synthesize`, or `pharaoh-rev-atomicity-split` is ready to persist into the project's advisory ledger. Wraps the emission into the engine's `RecoveryResult` shape (`reqs` -> `needs`, matching `RecoveredNeed`), writes it to a temp file, and runs `ubc agent reverse record --input <tempfile>` -- the only skill in the tree allowed to shell out to that command. `record` is the ledger's only writer and never touches RST. It does not apply cluster member up-links -- those are authored directly into RST by `pharaoh-rev-cluster-synthesize` (see that skill's `member_updates` output). Returns the CLI's JSON stdout unchanged.

See [`skills/pharaoh-rev-record-ledger/SKILL.md`](../../skills/pharaoh-rev-record-ledger/SKILL.md) for the full atomic specification -- inputs, outputs, atomicity contract, and composition patterns.

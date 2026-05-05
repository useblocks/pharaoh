---
description: Use when diffing two output directories produced by running the same plan twice to confirm the build is reproducible. Consumes a baseline directory, a rerun directory, and an optional list of mask rules for known-non-deterministic fields (timestamps, randomly-generated ids); emits a list of drifted files with per-file changed-field summaries. Does NOT run the plan — running is the caller's responsibility (`pharaoh-execute-plan`).
handoffs: []
---

# @pharaoh.reproducibility-check

Use when diffing two output directories produced by running the same plan twice to confirm the build is reproducible. Consumes a baseline directory, a rerun directory, and an optional list of mask rules for known-non-deterministic fields (timestamps, randomly-generated ids); emits a list of drifted files with per-file changed-field summaries. Does NOT run the plan — running is the caller's responsibility (`pharaoh-execute-plan`).

See [`skills/pharaoh-reproducibility-check/SKILL.md`](../../skills/pharaoh-reproducibility-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

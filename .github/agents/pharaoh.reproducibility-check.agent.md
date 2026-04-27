---
description: Diff two output directories produced by two runs of the same plan to confirm the build is reproducible. Consumes baseline dir, rerun dir, and optional mask rules for non-deterministic fields (timestamps, random ids); emits drifted-file list with per-file changed-field summaries. Does NOT run the plan — that is the caller's responsibility (`pharaoh-execute-plan`).
handoffs: []
---

# @pharaoh.reproducibility-check

Diff two output directories produced by running the same plan twice to confirm the build is reproducible. Consumes a baseline directory, a rerun directory, and an optional list of mask rules for known-non-deterministic fields (timestamps, randomly-generated ids); emits a list of drifted files with per-file changed-field summaries. Does NOT run the plan — running twice is the caller's responsibility (`pharaoh-execute-plan`).

See [`skills/pharaoh-reproducibility-check/SKILL.md`](../../skills/pharaoh-reproducibility-check/SKILL.md) for the full atomic specification — inputs, outputs, per-step process, failure modes, and composition patterns.

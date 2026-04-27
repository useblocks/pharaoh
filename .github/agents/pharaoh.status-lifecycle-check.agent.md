---
description: Release-gate check over a sphinx-needs corpus — counts needs still in the `draft` bucket (per workflows.yaml) and returns binary pass/fail when `enforce=true`. Advisory mode reports counts without failing.
handoffs:
  - label: Aggregate into quality gate
    agent: pharaoh.quality-gate
    prompt: Consume the status-lifecycle findings as the delegated check for the status-lifecycle-healthy invariant
---

# @pharaoh.status-lifecycle-check

Aggregate `status` across every need in `needs.json` against the `initial_state` declared in `workflows.yaml`. Binary release gate — under `enforce=true`, zero drafts pass, one draft fails. Under `enforce=false` (default), the findings are reported without failing so pre-release development is unblocked. Distinct from `pharaoh-lifecycle-check`, which evaluates per-need transition legality against `requires:` prerequisites.

See [`skills/pharaoh-status-lifecycle-check/SKILL.md`](../../skills/pharaoh-status-lifecycle-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

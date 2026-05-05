---
description: Use when running a release-gate check over a full sphinx-needs corpus to confirm that zero needs remain in the initial `draft` status. Single mechanical binary gate — aggregates `status` across every need in `needs.json`, compares against the initial-state declaration in `workflows.yaml`, and returns pass/fail plus per-status counts. Advisory by default (pre-release development passes); release pipelines override `enforce=true` so any draft blocks the gate.
handoffs:
  - label: Aggregate into quality gate
    agent: pharaoh.quality-gate
    prompt: Consume the status-lifecycle findings as the delegated check for the status-lifecycle-healthy invariant
---

# @pharaoh.status-lifecycle-check

Use when running a release-gate check over a full sphinx-needs corpus to confirm that zero needs remain in the initial `draft` status. Single mechanical binary gate — aggregates `status` across every need in `needs.json`, compares against the initial-state declaration in `workflows.yaml`, and returns pass/fail plus per-status counts. Advisory by default (pre-release development passes); release pipelines override `enforce=true` so any draft blocks the gate.

See [`skills/pharaoh-status-lifecycle-check/SKILL.md`](../../skills/pharaoh-status-lifecycle-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

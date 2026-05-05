---
description: Use when running the final validation step of any Pharaoh composition that emits artefacts (reqs, features, architecture elements). Consumes an aggregated review+mece+coverage summary plus a gate spec; returns pass/fail with named breaches. Never produces summaries itself — thin gate layer over upstream atomic checkers.
handoffs: []
---

# @pharaoh.quality-gate

Use when running the final validation step of any Pharaoh composition that emits artefacts (reqs, features, architecture elements). Consumes an aggregated review+mece+coverage summary plus a gate spec; returns pass/fail with named breaches. Never produces summaries itself — thin gate layer over upstream atomic checkers.

See [`skills/pharaoh-quality-gate/SKILL.md`](../../skills/pharaoh-quality-gate/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

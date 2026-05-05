---
description: Use when verifying that a Papyrus workspace actually received writes during a plan run. Single mechanical check — counts directives across `.papyrus/memory/*.rst` and returns pass/fail against a configured minimum. Wired into `pharaoh-quality-gate` to detect the "LLM-executor skipped the atomic Papyrus writes" failure class observed in prior dogfooding.
handoffs: []
---

# @pharaoh.papyrus-non-empty-check

Use when verifying that a Papyrus workspace actually received writes during a plan run. Single mechanical check — counts directives across `.papyrus/memory/*.rst` and returns pass/fail against a configured minimum. Wired into `pharaoh-quality-gate` to detect the "LLM-executor skipped the atomic Papyrus writes" failure class observed in prior dogfooding.

See [`skills/pharaoh-papyrus-non-empty-check/SKILL.md`](../../skills/pharaoh-papyrus-non-empty-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

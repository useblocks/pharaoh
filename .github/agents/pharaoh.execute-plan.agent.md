---
description: Use when executing a plan.yaml produced by pharaoh-write-plan. Reads the plan, runs each task (inline or via subagent dispatch), threads outputs between tasks per the ref grammar, validates outputs via pharaoh-output-validate, persists artefacts and report.yaml. Generic — the plan is the orchestrator, this skill is the engine.
handoffs: []
---

# @pharaoh.execute-plan

Use when executing a plan.yaml produced by pharaoh-write-plan. Reads the plan, runs each task (inline or via subagent dispatch), threads outputs between tasks per the ref grammar, validates outputs via pharaoh-output-validate, persists artefacts and report.yaml. Generic — the plan is the orchestrator, this skill is the engine.

See [`skills/pharaoh-execute-plan/SKILL.md`](../../skills/pharaoh-execute-plan/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

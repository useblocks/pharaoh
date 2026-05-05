---
description: Use when verifying that a plan's declared `execution_mode` matches observed subagent artefacts in `runs/`. Detects the "LLM-executor collapsed subagents into inline" failure class observed during dogfooding. One mechanical structural check.
handoffs: []
---

# @pharaoh.dispatch-signal-check

Use when verifying that a plan's declared `execution_mode` matches observed subagent artefacts in `runs/`. Detects the "LLM-executor collapsed subagents into inline" failure class observed during dogfooding. One mechanical structural check.

See [`skills/pharaoh-dispatch-signal-check/SKILL.md`](../../skills/pharaoh-dispatch-signal-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

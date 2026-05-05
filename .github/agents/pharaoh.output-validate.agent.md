---
description: Use when `pharaoh-execute-plan` (or any caller) has dispatched a subagent whose output must match one of the documented schemas (RST directive, sphinx-codelinks one-line comment, YAML mapping, JSON object). Returns {valid, errors, parsed, recovery}. Callers gate subagent output through this before writing anything to disk.
handoffs: []
---

# @pharaoh.output-validate

Use when `pharaoh-execute-plan` (or any caller) has dispatched a subagent whose output must match one of the documented schemas (RST directive, sphinx-codelinks one-line comment, YAML mapping, JSON object). Returns {valid, errors, parsed, recovery}. Callers gate subagent output through this before writing anything to disk.

See [`skills/pharaoh-output-validate/SKILL.md`](../../skills/pharaoh-output-validate/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

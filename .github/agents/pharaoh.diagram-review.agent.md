---
description: Use when auditing a single diagram block (Mermaid or PlantUML) emitted by any diagram-emitting skill. Single review atom covering all diagram types — trace/caption/element-count/parser/required-elements checks plus LLM-judge axes for purpose clarity and granularity consistency. Per-type required-element checks dispatched based on `diagram_type` input.
handoffs: []
---

# @pharaoh.diagram-review

Use when auditing a single diagram block (Mermaid or PlantUML) emitted by any diagram-emitting skill. Single review atom covering all diagram types — trace/caption/element-count/parser/required-elements checks plus LLM-judge axes for purpose clarity and granularity consistency. Per-type required-element checks dispatched based on `diagram_type` input.

See [`skills/pharaoh-diagram-review/SKILL.md`](../../skills/pharaoh-diagram-review/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

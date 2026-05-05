---
description: Use when running a terminal validation step over a directory of RST files to catch Mermaid / PlantUML parse failures that sphinx-build cannot detect. Extracts every `.. mermaid::` and `.. uml::` block and pipes it to the real renderer parser (mmdc / plantuml -checkonly). Returns structured findings. Does NOT modify the RST files.
handoffs:
  - label: Aggregate into quality gate
    agent: pharaoh.quality-gate
    prompt: Consume the diagram-lint findings alongside review/mece/coverage reports for the terminal pass/fail decision
---

# @pharaoh.diagram-lint

Use when running a terminal validation step over a directory of RST files to catch Mermaid / PlantUML parse failures that sphinx-build cannot detect. Extracts every `.. mermaid::` and `.. uml::` block and pipes it to the real renderer parser (mmdc / plantuml -checkonly). Returns structured findings. Does NOT modify the RST files.

See [`skills/pharaoh-diagram-lint/SKILL.md`](../../skills/pharaoh-diagram-lint/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

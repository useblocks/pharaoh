---
description: Walk a directory of RST files and check every `.. mermaid::` / `.. uml::` block against the real renderer parser (mmdc, plantuml). Catches silent parse failures that sphinx-build misses.
handoffs:
  - label: Aggregate into quality gate
    agent: pharaoh.quality-gate
    prompt: Consume the diagram-lint findings alongside review/mece/coverage reports for the terminal pass/fail decision
---

# @pharaoh.diagram-lint

Walk a directory of RST files, extract every Mermaid / PlantUML block, and parse each block with the real renderer CLI (`mmdc -i tmp.mmd -o /dev/null`, `plantuml -checkonly`). Emits structured findings. Read-only — does not modify RST. When a renderer CLI is unavailable, degrades gracefully with a warning and install command.

See [`skills/pharaoh-diagram-lint/SKILL.md`](../../skills/pharaoh-diagram-lint/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

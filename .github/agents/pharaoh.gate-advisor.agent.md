---
description: Read a project's `pharaoh.toml` and report which phased-enablement ladder step is the recommended next gate to switch on. Advisory, read-only — walks the fixed 5-step ladder in order (`require_verification` → `require_change_analysis` → `require_mece_on_release` → `codelinks.enabled` → `strictness = "enforcing"`) and names the first unmet step plus its blocker.
handoffs: []
---

# @pharaoh.gate-advisor

Read the project's `pharaoh.toml`, parse the five ladder flags, and emit a findings JSON naming the next recommended gate to enable, the blocker that must be cleared first, and the full fixed ladder. Read-only; never edits `pharaoh.toml`. The ladder rationale lives in [`skills/shared/gate-enablement.md`](../../skills/shared/gate-enablement.md) — this atom is the tool that walks it, not the authority that defines it.

See [`skills/pharaoh-gate-advisor/SKILL.md`](../../skills/pharaoh-gate-advisor/SKILL.md) for the full atomic specification — inputs, outputs, per-step process, ladder table, rationale map, tailoring extension point, and composition patterns.

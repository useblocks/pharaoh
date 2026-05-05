---
description: Use when reading a project's `pharaoh.toml` to report which phased-enablement ladder step is the recommended next gate to switch on. Single mechanical advisory check — parses five flags (`strictness`, `require_verification`, `require_change_analysis`, `require_mece_on_release`, `codelinks.enabled`), walks the fixed ladder in order, and emits the first unmet step plus its blocker note. Read-only; never edits `pharaoh.toml`.
handoffs: []
---

# @pharaoh.gate-advisor

Use when reading a project's `pharaoh.toml` to report which phased-enablement ladder step is the recommended next gate to switch on. Single mechanical advisory check — parses five flags (`strictness`, `require_verification`, `require_change_analysis`, `require_mece_on_release`, `codelinks.enabled`), walks the fixed ladder in order, and emits the first unmet step plus its blocker note. Read-only; never edits `pharaoh.toml`.

See [`skills/pharaoh-gate-advisor/SKILL.md`](../../skills/pharaoh-gate-advisor/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

---
description: Use when a requirement has been drafted (either as an RST block by `pharaoh-req-from-code` or implicitly) and you need to insert a one-line comment into the source file that carries the trace. Two modes — `codelinks` (sphinx-codelinks-compatible multi-field `@ title, id, type, [links]` form; the comment IS the need) and `backref` (minimal `@req ID: title` pointer back to an RST-hosted need). Mode is tailored via `ubproject.toml` / `pharaoh.toml`, not hardcoded.
handoffs: []
---

# @pharaoh.req-codelink-annotate

Use when a requirement has been drafted (either as an RST block by `pharaoh-req-from-code` or implicitly) and you need to insert a one-line comment into the source file that carries the trace. Two modes — `codelinks` (sphinx-codelinks-compatible multi-field `@ title, id, type, [links]` form; the comment IS the need) and `backref` (minimal `@req ID: title` pointer back to an RST-hosted need). Mode is tailored via `ubproject.toml` / `pharaoh.toml`, not hardcoded.

See [`skills/pharaoh-req-codelink-annotate/SKILL.md`](../../skills/pharaoh-req-codelink-annotate/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

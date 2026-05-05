---
description: Use when verifying that a source file is covered by the need catalogue on two axes — (1) at least one CREQ declares the file as its `:source_doc:`, and (2) every project-defined exception class raised in the file is named by some CREQ's title or content. Exception classes not defined in the project source tree (stdlib, third-party deps) are reported as `external` and do not fail the axis. Classifies non-behavioral files (constants, type aliases, bare re-exports) as skipped. Language-parametric via the shared regex table in `skills/shared/public-symbol-patterns.md` (python / rust / typescript / go / c / cpp / java). Single mechanical structural check.
handoffs: []
---

# @pharaoh.api-coverage-check

Use when verifying that a source file is covered by the need catalogue on two axes — (1) at least one CREQ declares the file as its `:source_doc:`, and (2) every project-defined exception class raised in the file is named by some CREQ's title or content. Exception classes not defined in the project source tree (stdlib, third-party deps) are reported as `external` and do not fail the axis. Classifies non-behavioral files (constants, type aliases, bare re-exports) as skipped. Language-parametric via the shared regex table in `skills/shared/public-symbol-patterns.md` (python / rust / typescript / go / c / cpp / java). Single mechanical structural check.

See [`skills/pharaoh-api-coverage-check/SKILL.md`](../../skills/pharaoh-api-coverage-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

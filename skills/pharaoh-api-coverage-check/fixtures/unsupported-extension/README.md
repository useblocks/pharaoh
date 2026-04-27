# unsupported-extension

The source is `.lua`, which does not appear in the globs column of `skills/shared/public-symbol-patterns.md`. With `language: "auto"` the resolver fails. The skill emits `overall: "fail"` with `language: "unknown"`, `classification: "non-behavioral"`, both sub-axes carrying `passed: null`, and `blockers: ["unsupported language: .lua"]`. The project either adds a row to the shared table or passes an explicit `language` override (see `language-override` fixture).

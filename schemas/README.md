# Pharaoh tailoring schemas

JSON Schemas (Draft 2020-12) for the four tailoring files Pharaoh
authors and consumes:

| File                                  | Validates                                  | Authored by                           | Consumed by                                    |
|---------------------------------------|--------------------------------------------|---------------------------------------|------------------------------------------------|
| `artefact-catalog.schema.json`        | `.pharaoh/project/artefact-catalog.yaml`   | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review`, `pharaoh-link-completeness-check`, `pharaoh-output-validate`, `pharaoh-review-completeness` |
| `workflows.schema.json`               | `.pharaoh/project/workflows.yaml`          | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review`, `pharaoh-lifecycle-check`, `pharaoh-status-lifecycle-check` |
| `id-conventions.schema.json`          | `.pharaoh/project/id-conventions.yaml`     | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review`, `pharaoh-id-convention-check`, `pharaoh-id-allocate` |
| `checklists-frontmatter.schema.json`  | `.pharaoh/project/checklists/*.md` (frontmatter only) | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review` |

`pharaoh-tailor-review` resolves the schema set in this order:

1. Explicit `schemas_dir` argument from the caller.
2. `<tailoring_dir>/schemas/` if present in the project (per-project overrides).
3. The Pharaoh-shipped `schemas/` directory (this folder).
4. Built-in structural rules (degraded mode — emits a warning).

Per-project overrides may add fields, never remove required ones.

To extend: add a property to the schema, then update the matching emitter (`pharaoh-tailor-bootstrap` or `pharaoh-tailor-fill`) to populate it. Cross-file referential checks (every lifecycle state in artefact-catalog must appear in workflows; every prefix in artefact-catalog must appear in id-conventions) are enforced by `pharaoh-tailor-review` as cross-file rules C1-C5, not by JSON Schema.

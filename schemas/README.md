# Pharaoh tailoring schemas

JSON Schemas (Draft 2020-12) for the four tailoring files Pharaoh
authors and consumes:

| File                                  | Validates                                  | Authored by                           | Consumed by                                    |
|---------------------------------------|--------------------------------------------|---------------------------------------|------------------------------------------------|
| `artefact-catalog.schema.json`        | `.pharaoh/project/artefact-catalog.yaml`   | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review`, `pharaoh-link-completeness-check`, `pharaoh-output-validate`, `pharaoh-review-completeness`, `pharaoh-quality-gate` |
| `workflows.schema.json`               | `.pharaoh/project/workflows.yaml`          | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review`, `pharaoh-lifecycle-check`, `pharaoh-status-lifecycle-check` |
| `id-conventions.schema.json`          | `.pharaoh/project/id-conventions.yaml`     | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review`, `pharaoh-id-convention-check`, `pharaoh-id-allocate` |
| `checklists-frontmatter.schema.json`  | `.pharaoh/project/checklists/*.md` (frontmatter only) | `pharaoh-tailor-bootstrap`, `pharaoh-tailor-fill` | `pharaoh-tailor-review` |

`pharaoh-tailor-review` resolves the schema set in this order:

1. Explicit `schemas_dir` argument from the caller.
2. `<tailoring_dir>/schemas/` if present in the project (per-project overrides).
3. The Pharaoh-shipped `schemas/` directory (this folder).
4. Built-in structural rules (degraded mode — emits a warning).

Per-project overrides may add fields, never remove required ones.

To extend: add a property to the schema, then update the matching emitter (`pharaoh-tailor-bootstrap` or `pharaoh-tailor-fill`) to populate it. Cross-file referential checks (every lifecycle state in artefact-catalog must appear in workflows; every prefix in artefact-catalog must appear in id-conventions) are enforced by `pharaoh-tailor-review` as cross-file rules C1-C6, not by JSON Schema.

The four release-gate fields on each per-type entry of `artefact-catalog.yaml` (`required_links`, `optional_links`, `required_metadata_fields`, `required_roles`) are all optional in the schema but their absence is surfaced as a finding by `pharaoh-tailor-review` rule C6 — empty arrays declare an explicit "no requirement" choice, missing keys mean the project never decided. Consumers (`pharaoh-link-completeness-check`, `pharaoh-output-validate`, `pharaoh-review-completeness`) treat absent keys as empty so a project with none of these fields ships a silent no-op release gate; rule C6 is what makes the choice explicit.

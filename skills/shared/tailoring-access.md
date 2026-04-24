# tailoring-access

Shared helper module documenting how Pharaoh skills resolve project tailoring paths. Referenced by `pharaoh-req-draft`, `pharaoh-req-regenerate`, `pharaoh-arch-draft`, `pharaoh-vplan-draft`, and any other skill whose input includes `tailoring_path`.

## Resolution order

Given a `tailoring_path` input (typically the absolute path to `.pharaoh/project/`):

1. **Artefact catalogue**: read `<tailoring_path>/artefact-catalog.yaml`. Contains `required_fields`, `optional_fields`, `child_of`, and `lifecycle_ref` per declared type. Produced by `pharaoh-tailor-bootstrap` or hand-authored.
2. **ID conventions**: read `<tailoring_path>/id-conventions.yaml`. Contains `prefixes` (directive → prefix map), `id_regex` (validation regex), `separator`. Produced by `pharaoh-tailor-bootstrap`.
3. **Workflows**: read `<tailoring_path>/workflows.yaml`. Per-type state machine (`states`, `transitions`, `initial`, `final`). Produced by `pharaoh-tailor-bootstrap`.
4. **Checklists**: read `<tailoring_path>/checklists/<directive>.md` for per-type checklists. Use `<tailoring_path>/checklists/requirement.md` as the canonical-alias filename when the caller wants "the" requirement checklist without knowing the project's directive name (alias is emitted by `pharaoh-tailor-bootstrap`).
5. **Project-level config** (outside tailoring path, but same resolution family): `<project_root>/ubproject.toml` defines `[[needs.types]]` and `[[needs.extra_links]]` used upstream by `pharaoh-tailor-bootstrap`. `<project_root>/pharaoh.toml` carries the strictness setting read by orchestrators (see `shared/strictness.md`).

## Fallback behaviour

A missing file is not automatically an error — each calling skill documents whether it requires the file strictly or falls back to built-in defaults. Skills that operate without tailoring MUST emit a `"note"` in their output naming the missing file and the default applied, so the caller can tell tailored runs apart from fallback runs.

## Non-goals

This helper does not read or parse the files; it only documents resolution order. Each skill does its own YAML / TOML parse and validation.

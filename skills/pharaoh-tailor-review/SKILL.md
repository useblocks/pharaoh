---
name: pharaoh-tailor-review
description: Use when auditing .pharaoh/project/ tailoring files against JSON schemas (id-conventions, workflows, artefact-catalog, checklists frontmatter) plus cross-file consistency checks (every lifecycle state referenced in artefact-catalog exists in workflows.yaml, every prefix in artefact-catalog is declared in id-conventions, etc.).
chains_from: [pharaoh-tailor-fill]
chains_to: [pharaoh-tailor-fill]
---

# pharaoh-tailor-review

## When to use

Invoke after `pharaoh-tailor-fill` has written the four tailoring files, or whenever the files
are manually edited and need re-validation.

This skill validates structure and cross-file consistency. It does NOT judge whether the
conventions are sensible — it checks whether they are internally coherent and well-formed.

Do NOT invoke to author or repair tailoring files — use `pharaoh-tailor-fill` for that.

---

## Inputs

- **tailoring_dir** (from user): path to `.pharaoh/project/` containing the four tailoring
  files
- **schemas_dir** (from user, optional): path to JSON schema files. Resolved in
  this order:
    1. The explicit value if provided.
    2. `<tailoring_dir>/schemas/` if that directory exists (per-project overrides).
    3. The Pharaoh-shipped `schemas/` directory at the package root
       (`<pharaoh_repo>/schemas/`). This is the default and ships with the four
       canonical schemas (`artefact-catalog.schema.json`, `workflows.schema.json`,
       `id-conventions.schema.json`, `checklists-frontmatter.schema.json`).
    4. If none of the above resolve, falls back to built-in structural rules and
       emits a `degraded_mode: true` flag in the output.

The four expected files:
- `<tailoring_dir>/id-conventions.yaml`
- `<tailoring_dir>/workflows.yaml`
- `<tailoring_dir>/artefact-catalog.yaml`
- `<tailoring_dir>/checklists/requirement.md`

---

## Outputs

A single JSON document — no prose wrapper. Shape:

```json
{
  "tailoring_dir": "/path/to/.pharaoh/project",
  "files_checked": 4,
  "schema_violations": {
    "id-conventions.yaml": [],
    "workflows.yaml": [],
    "artefact-catalog.yaml": [],
    "checklists/requirement.md": []
  },
  "cross_file_violations": [],
  "overall": "pass"
}
```

Each violation entry:

```json
{
  "file": "artefact-catalog.yaml",
  "rule": "prefix_declared_in_id_conventions",
  "detail": "Prefix 'tc' appears in artefact-catalog.yaml but is not declared in id-conventions.yaml prefixes map",
  "severity": "error"
}
```

`overall` values:
- `"pass"` — zero violations across all checks
- `"warnings_only"` — violations with `"severity": "warning"` only
- `"fail"` — at least one `"severity": "error"` violation

---

## Process

### Step 1: Load and parse all four files

Read each file. If any required file is missing, record a `severity: error` violation and
continue checking the remaining files:

```json
{
  "file": "<filename>",
  "rule": "file_present",
  "detail": "File not found at <path>",
  "severity": "error"
}
```

Parse YAML files with a strict parser. If a file is syntactically invalid YAML, record:

```json
{
  "file": "<filename>",
  "rule": "yaml_syntax",
  "detail": "YAML parse error: <error message>",
  "severity": "error"
}
```

Do not attempt cross-file checks for a file that failed to parse.

---

### Step 2: Schema validation per file

Apply the following structural rules. These are built-in; external JSON schemas supplement
but do not replace them.

**id-conventions.yaml required keys:**

| Key | Type | Rule |
|---|---|---|
| `separator` | string | Must be present |
| `id_regex` | string | Must be present; non-empty |
| `prefixes` | map | Must be present; must contain at least one entry |
| `id_regex_exceptions` | map | Optional; if present must be a map of `<prefix>: <regex>` where `<prefix>` is declared in the `prefixes` map |

For each entry in `prefixes`, the key must be a non-empty string and the value must be
a literal identifier-prefix token (matches schema pattern `^[A-Za-z][A-Za-z0-9_]*$`);
not a human description. See
`<pharaoh_repo>/schemas/id-conventions.schema.json` for the authoritative
JSON Schema.

**workflows.yaml required keys:**

| Key | Type | Rule |
|---|---|---|
| `lifecycle_states` | array of strings | Must be present; at least two unique, non-empty state names |
| `transitions` | list | Must be present; may be empty |

For each transition in `transitions`:
- Must have `from`, `to`, `requires` keys.
- `from` and `to` must be non-empty strings.
- `requires` must be a list (may be empty).

See `<pharaoh_repo>/schemas/workflows.schema.json` for the authoritative
JSON Schema.

**artefact-catalog.yaml required structure:**

Top level must be a map of artefact-type keys. For each artefact type:

| Key | Type | Rule |
|---|---|---|
| `required_fields` | list | Must be present; must include at least `id` and `status`. Entries are sphinx-needs *option* keys (`:key: value`). |
| `optional_fields` | list | Optional; may be empty. Entries are sphinx-needs *option* keys. |
| `required_body_sections` | list | Optional; entries are top-level heading names that must appear inside the directive body prose (e.g. `Inputs`, `Steps`, `Expected` for `tc`). Validated as body prose, not as `:key:` options. |
| `lifecycle` | list | Optional; if present must be non-empty |
| `required_links` | list | Optional; entries are link-relation option names (e.g. `satisfies`). Empty list disables the release-gate check for this type; absent key is treated as empty by `pharaoh-link-completeness-check` but flagged by C6 below. |
| `optional_links` | list | Optional; entries are link-relation option names. Must not overlap with `required_links` (enforced by C6). |
| `required_metadata_fields` | list | Optional; entries are sphinx-needs option keys. Empty list disables the release-gate check; absent key is flagged by C6. |
| `required_roles` | list | Optional; entries are role-bearing option keys (e.g. `reviewer`, `approved_by`). Empty list explicitly declares no review/approval gate; absent key is flagged by C6. |

See `<pharaoh_repo>/schemas/artefact-catalog.schema.json` for the
authoritative JSON Schema.

**checklists/*.md frontmatter:**

YAML frontmatter (delimited by `---`) at the top of a checklist file is **optional**. When
present, it is validated against
`<pharaoh_repo>/schemas/checklists-frontmatter.schema.json`:

| Key | Rule |
|---|---|
| `name` | Optional; non-empty string if present |
| `applies_to` | Optional; artefact-type key from `artefact-catalog.yaml`, or `"*"` |
| `axes` | Optional; list of one or more non-empty axis labels |

Additional fields are allowed (`additionalProperties: true`). Do NOT error on a missing
frontmatter block or on missing individual keys; only error on fields that are *present* but
violate the type rule above.

---

### Step 3: Cross-file consistency checks

Run these checks after all four files are parsed successfully.

**C1 — Prefix declared in id-conventions for every type in artefact-catalog**

For every key in `artefact-catalog.yaml`, that key must also appear in
`id-conventions.yaml.prefixes`.

Violation (error) if not:
```
Prefix '<key>' appears in artefact-catalog.yaml but is not declared in id-conventions.yaml prefixes map.
```

**C2 — Lifecycle states in artefact-catalog exist in workflows.yaml**

For every artefact type in `artefact-catalog.yaml` that carries a `lifecycle` list, every
state value must appear as an entry in the `workflows.yaml.lifecycle_states` array.

Violation (error) if not:
```
Lifecycle state '<state>' referenced in artefact-catalog.yaml (<type>.lifecycle) is not declared in workflows.yaml lifecycle_states.
```

**C3 — Transition states exist in lifecycle_states**

For every transition in `workflows.yaml.transitions`, both `from` and `to` must appear as
entries in the `workflows.yaml.lifecycle_states` array.

Violation (error) if not:
```
Transition from='<from>' to='<to>' references state '<state>' which is not declared in workflows.yaml lifecycle_states.
```

**C4 — id-conventions prefix superset of artefact-catalog**

Every prefix declared in `id-conventions.yaml.prefixes` should appear in
`artefact-catalog.yaml`. A prefix with no catalog entry is not an error but should be flagged
as a warning — the tailoring is incomplete for that type.

Violation (warning):
```
Prefix '<key>' declared in id-conventions.yaml but has no entry in artefact-catalog.yaml. Add a catalog entry or remove the prefix declaration.
```

**C5 — required_fields does not overlap optional_fields**

For each artefact type, no field name should appear in both `required_fields` and
`optional_fields`.

Violation (error):
```
Field '<field>' appears in both required_fields and optional_fields for artefact type '<type>' in artefact-catalog.yaml.
```

**C6 — Release-gate fields declared explicitly**

The four release-gate fields on each per-type entry of `artefact-catalog.yaml` are
consumed by `pharaoh-link-completeness-check` (`required_links`, `optional_links`),
`pharaoh-output-validate` (`required_metadata_fields`), and `pharaoh-review-completeness`
(`required_roles`); all four are aggregated by `pharaoh-quality-gate`. Each consumer
treats an absent key as an empty list, so a project that omits all four fields ships a
release gate that silently does nothing. C6 makes the choice explicit:

For every artefact type entry in `artefact-catalog.yaml`, three of the four fields must
be **present as keys** (the value may be an empty array). The three keys are
`required_links`, `required_metadata_fields`, `required_roles`. `optional_links` is
not part of C6 — it is purely informational and absent-equals-empty is fine.

Violation (warning) for each missing key:
```
Release-gate key '<field>' is absent from artefact-catalog.yaml for type '<type>'. Empty array declares an explicit "no requirement"; missing key is treated as empty by consumers but means the project never made the choice. Add the key with an empty list `[]` if no requirement applies.
```

Where `<field>` is one of `required_links`, `required_metadata_fields`, `required_roles`.

Additionally — when both `required_links` and `optional_links` are present, no link
name may appear in both lists.

Violation (error):
```
Link name '<link>' appears in both required_links and optional_links for artefact type '<type>' in artefact-catalog.yaml.
```

The missing-key part of C6 is a `severity: warning` rather than `error` so that legacy
tailoring continues to validate while the project decides; the overlap-check part is
`severity: error` because consumers cannot reconcile a link declared as both required
and optional.

---

### Step 4: Compute overall and emit

Determine `overall`:
- `"fail"` if any violation has `severity: error`
- `"warnings_only"` if all violations have `severity: warning`
- `"pass"` if `schema_violations` and `cross_file_violations` are both empty

Emit the JSON document. No prose before or after.

---

## Schema validation

Four JSON Schema (draft 2020-12) files ship with Pharaoh and make structural
validation deterministic:

| Tailoring file | Schema |
|---|---|
| `id-conventions.yaml` | `<schemas_dir>/id-conventions.schema.json` |
| `workflows.yaml` | `<schemas_dir>/workflows.schema.json` |
| `artefact-catalog.yaml` | `<schemas_dir>/artefact-catalog.schema.json` |
| `checklists/*.md` (frontmatter) | `<schemas_dir>/checklists-frontmatter.schema.json` |

`<schemas_dir>` is resolved per the order documented in Inputs above; the
default is the Pharaoh-shipped `schemas/` directory at the package root. See
`schemas/README.md` for the full resolution order and per-file responsibilities.

Schema `$id` values are anchored under `https://pharaoh.useblocks.com/schemas/` and do not
need to resolve at runtime.

These checks can be executed by any JSON Schema validator against the canonical
schemas in `schemas/`. Cross-file consistency rules C1–C6 are **not** expressible in
JSON Schema and remain implemented in Step 3 of this skill.

---

## Guardrails

**G1 — All four files missing**

If none of the four files are found, the tailoring_dir may be wrong. FAIL before attempting
any checks:

```
FAIL: No tailoring files found at <tailoring_dir>.
Expected: id-conventions.yaml, workflows.yaml, artefact-catalog.yaml, checklists/requirement.md.
Verify the path or run pharaoh-tailor-fill first.
```

**G2 — Partial file set**

If some but not all files exist, proceed with the available files and record file_present
errors for the missing ones. Do not FAIL outright.

**G3 — Malformed JSON output**

If the emitted JSON is malformed, self-correct once. If still malformed, emit raw findings as
free text with a `[DIAGNOSTIC]` prefix.

---

## Advisory chain

If `overall` is `"fail"` or `"warnings_only"`, append after the JSON:

```
Run `pharaoh-tailor-fill` with `overwrite_ok: true` to regenerate the affected files,
or edit them manually and re-run pharaoh-tailor-review.
```

---

## Worked example

**User input:** `tailoring_dir = /work/eclipse-score/.pharaoh/project/`

All four files present and well-formed. Cross-file check results:
- C1: all artefact-catalog types (`gd_req`, `gd_chklst`, `std_req`, `tc`, `wf`, `wp`) are
  declared in id-conventions. Pass.
- C2: lifecycle `[draft, valid, inspected]` on `gd_req`, `tc`, `arch` — all three states are
  keys in workflows.yaml. Pass.
- C3: all transitions reference only `draft`, `valid`, `inspected`. Pass.
- C4: all six prefixes in id-conventions also appear in artefact-catalog. No orphan prefixes.
  Pass.
- C5: no field appears in both required and optional for any type. Pass.
- C6: every artefact type declares `required_links`, `required_metadata_fields`, and
  `required_roles` keys (empty arrays permitted). Pass.

**Output:**

```json
{
  "tailoring_dir": "/work/eclipse-score/.pharaoh/project",
  "files_checked": 4,
  "schema_violations": {
    "id-conventions.yaml": [],
    "workflows.yaml": [],
    "artefact-catalog.yaml": [],
    "checklists/requirement.md": []
  },
  "cross_file_violations": [],
  "overall": "pass"
}
```

**Variant — one cross-file error:**

`artefact-catalog.yaml` contains an `arch` type entry that is not declared in
`id-conventions.yaml` prefixes (the fill step missed it).

```json
{
  "tailoring_dir": "/work/eclipse-score/.pharaoh/project",
  "files_checked": 4,
  "schema_violations": {
    "id-conventions.yaml": [],
    "workflows.yaml": [],
    "artefact-catalog.yaml": [],
    "checklists/requirement.md": []
  },
  "cross_file_violations": [
    {
      "file": "artefact-catalog.yaml",
      "rule": "prefix_declared_in_id_conventions",
      "detail": "Prefix 'arch' appears in artefact-catalog.yaml but is not declared in id-conventions.yaml prefixes map",
      "severity": "error"
    }
  ],
  "overall": "fail"
}
```

```
Run `pharaoh-tailor-fill` with `overwrite_ok: true` to regenerate the affected files,
or edit them manually and re-run pharaoh-tailor-review.
```

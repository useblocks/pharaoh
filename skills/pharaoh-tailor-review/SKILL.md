---
name: pharaoh-tailor-review
description: Audit .pharaoh/project/ tailoring files against JSON schemas (id-conventions, workflows, artefact-catalog, checklists frontmatter) plus cross-file consistency checks (every lifecycle state referenced in artefact-catalog exists in workflows.yaml, every prefix in artefact-catalog is declared in id-conventions, etc.).
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
- **schemas_dir** (from user, optional): path to JSON schema files. Defaults to
  `<tailoring_dir>/schemas/` if that directory exists; otherwise applies built-in structural
  checks (see Step 2).

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
| `separator` | string or null | Must be present; string if set |
| `id_regex` | string or null | Must be present |
| `prefixes` | map | Must be present; must contain at least one entry |
| `id_regex_exceptions` | map | Must be present; may be empty (`{}`) |

For each entry in `prefixes`, the key must be a non-empty string and the value must be a
non-empty string (the description).

**workflows.yaml required keys:**

| Key | Type | Rule |
|---|---|---|
| `lifecycle_states` | map | Must be present; at least one state |
| `transitions` | list | Must be present; may be empty |

For each transition in `transitions`:
- Must have `from`, `to`, `requires` keys.
- `from` and `to` must be non-empty strings.
- `requires` must be a list (may be empty).

**artefact-catalog.yaml required structure:**

Top level must be a map of artefact-type keys. For each artefact type:

| Key | Type | Rule |
|---|---|---|
| `required_fields` | list | Must be present; must include at least `id` and `status` |
| `optional_fields` | list | Must be present; may be empty |
| `lifecycle` | list | Optional; if present must be non-empty |

**checklists/requirement.md frontmatter:**

The file must start with a YAML frontmatter block (delimited by `---`). The frontmatter must
contain:

| Key | Rule |
|---|---|
| `title` | Non-empty string |
| `standard` | One of: `iso26262-8.6`, `aspice-4.0`, `iso21434`, or a custom string |
| `axes` | Map with at least one sub-key (`individual`, `set_level`, or `chain_level`) |

If frontmatter is missing or any key absent, record a `severity: error` violation.

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
state value must appear as a key in `workflows.yaml.lifecycle_states`.

Violation (error) if not:
```
Lifecycle state '<state>' referenced in artefact-catalog.yaml (<type>.lifecycle) is not declared in workflows.yaml lifecycle_states.
```

**C3 — Transition states exist in lifecycle_states**

For every transition in `workflows.yaml.transitions`, both `from` and `to` must appear as
keys in `workflows.yaml.lifecycle_states`.

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

---

### Step 4: Compute overall and emit

Determine `overall`:
- `"fail"` if any violation has `severity: error`
- `"warnings_only"` if all violations have `severity: warning`
- `"pass"` if `schema_violations` and `cross_file_violations` are both empty

Emit the JSON document. No prose before or after.

---

## Schema validation

Four JSON Schema (draft 2020-12) files live alongside the tailoring files and make structural
validation deterministic:

| Tailoring file | Schema |
|---|---|
| `id-conventions.yaml` | `<tailoring_dir>/schemas/id-conventions.schema.json` |
| `workflows.yaml` | `<tailoring_dir>/schemas/workflows.schema.json` |
| `artefact-catalog.yaml` | `<tailoring_dir>/schemas/artefact-catalog.schema.json` |
| `checklists/*.md` (frontmatter) | `<tailoring_dir>/schemas/checklists-frontmatter.schema.json` |

Schema `$id` values are anchored under `https://pharaoh.useblocks.com/schemas/` and do not
need to resolve at runtime.

The `pharaoh-validation` harness runs `python harness/validate_tailoring.py` to execute
these checks mechanically (exits 0 on all-PASS). Cross-file consistency rules C1–C5 are
**not** expressible in JSON Schema and remain implemented in Step 3 of this skill.

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

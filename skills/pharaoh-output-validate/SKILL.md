---
name: pharaoh-output-validate
description: Use when `pharaoh-execute-plan` (or any caller) has dispatched a subagent whose output must match one of the documented schemas (RST directive, sphinx-codelinks one-line comment, YAML mapping, JSON object). Returns {valid, errors, parsed, recovery}. Callers gate subagent output through this before writing anything to disk.
---

# pharaoh-output-validate

## When to use

Invoke from `pharaoh-execute-plan` after each dispatched task returns, to check that the task's raw output matches the emitting skill's declared `## Output schema` section. Also invoke directly from any other skill or human checking emitted content. Reject output that fails validation; optionally retry with stricter prompt; never write drifted output to disk.

Do NOT use to generate output (that is the emitting skill). Do NOT use to parse output that already passed validation (the `parsed` field carries the structured form for you).

## Atomicity

- (a) Indivisible — one target description in → one validation result out. The atom has a single responsibility: **"validate required fields for this artefact type are present and well-formed."** Two input shapes are exposed via the `mode` input:
  - `mode: "block"` (default; backward-compatible): one output string + one target schema + schema context. Validates one directive block against a declared schema.
  - `mode: "graph"`: one `needs.json` + one `artefact-catalog.yaml` path. Validates every need's tailored `required_metadata_fields` across the full graph.

  The mode toggle selects the input shape — it does NOT add a second responsibility. In both modes the atom asks the same question per-artefact ("does this need carry the required fields declared for its type?") and returns the same verdict axis. No mutation of inputs. No re-dispatch. No logging beyond the structured return.
- (b) Input:
  - block mode: `{mode?: "block", output_text: str, target_schema: "rst_directive"|"codelinks_comment"|"yaml_map"|"json_obj", schema_context: dict, strip_fences?: bool}`. `schema_context` fields vary per `target_schema`; documented in `## Schema context`.
  - graph mode: `{mode: "graph", needs_json_path: str, artefact_catalog_path: str}`.

  Output (shared shape; `parsed` / `recovery` are block-mode-only):
  - block mode: `{valid: bool, errors: list[str], parsed: object|null, recovery: {stripped_text: str|null}}`.
  - graph mode: `{valid: bool, errors: list[str], needs_checked: int, violations: [{need_id, type, missing_fields: [str]}]}`.
- (c) Reward: block-mode fixtures in `pharaoh-validation/fixtures/pharaoh-output-validate/` + graph-mode fixtures in `skills/pharaoh-output-validate/fixtures/`.

  Block-mode (4 fixtures):
  1. `sample_clean.rst` with `target_schema="rst_directive"`, `schema_context={directive: "feat", required_options: ["id", "status", "source_doc"]}` → `valid=true`, `parsed` contains one block with the expected fields.
  2. `sample_fenced.md` with the same schema → `valid=false` without `strip_fences`; with `strip_fences=true` → `valid=true` and `recovery.stripped_text` set.
  3. `sample_prose_wrapped.rst` → `valid=false` regardless of `strip_fences` (prose is not a fence). Errors name the surrounding prose.
  4. `sample_typo_option.rst` with `schema_context={directive: "comp_req", required_options: ["id", "status"], allowed_options: ["id", "status", "satisfies"]}` → `valid=false`. Errors name `subsatisfies` as unknown.

  Graph-mode (3 fixtures in `skills/pharaoh-output-validate/fixtures/`):
  5. `graph-all-metadata-present/` — catalog declares `required_metadata_fields` for each type; every need carries every field non-empty → `valid=true`, empty `violations`.
  6. `graph-missing-tags/` — catalog declares `:tags:` required for `comp_req`; several `comp_req` needs lack `tags` → `valid=false`, `violations` lists the offenders with `missing_fields: ["tags"]`.
  7. `graph-empty-required-list/` — catalog declares `required_metadata_fields: []` (or omits the key) for a type; that type's needs carry no metadata → `valid=true` (nothing to check).

  Pass = all 7 produce the stated result.
- (d) Reusable: any composition skill that dispatches emission subagents needs this.
- (e) Composable: this skill never calls emission skills back. It is purely a parser.

## Input

- `mode` (optional, default `"block"`): one of `"block"` or `"graph"`. Selects the input shape and processing branch. Existing callers that omit `mode` get block mode — fully backward-compatible.

### Block-mode fields (used when `mode == "block"`)

- `output_text`: the raw text the subagent returned. May include prefixes like `# emit=rst` from `pharaoh-req-from-code` — the validator strips documented prefixes before parsing.
- `target_schema`: one of:
  - `"rst_directive"` — expect one or more RST directive blocks per `pharaoh-req-from-code`'s Output schema Stage 1 / Stage 2 regex.
  - `"codelinks_comment"` — expect one or more sphinx-codelinks one-line comments parseable by the tailored `oneline_comment_style`.
  - `"yaml_map"` — expect a YAML document with a specific top-level key shape.
  - `"json_obj"` — expect a JSON object with specific required keys.
- `schema_context`: schema-specific context. See `## Schema context`.
- `strip_fences` (optional, default `false`): if `true`, one automatic recovery attempt strips a leading/trailing triple-backtick fence (with optional language hint) before re-validating.

### Graph-mode fields (used when `mode == "graph"`)

- `needs_json_path`: absolute path to the built sphinx-needs corpus `needs.json`. Accepts either the flat `{"needs": {<id>: {...}, ...}}` shape or the versioned `{"versions": {"<v>": {"needs": {...}}}}` shape (uses `current_version` if declared, else the latest key).
- `artefact_catalog_path`: absolute path to `.pharaoh/project/artefact-catalog.yaml`. Each top-level key is a need `type`; the validator reads `required_metadata_fields: [<field_name>, ...]` per type. Empty list → no metadata check for that type. Absent key → treated as empty (no check, not an error).

## Schema context

Per `target_schema`:

- `"rst_directive"`: `{directive: str, required_options: list[str], allowed_options?: list[str], parent_ids?: list[str]}`. `allowed_options` extends the built-in sphinx-needs options + `source_doc` Pharaoh convention. If `parent_ids` is non-empty, the validator checks that `satisfies` (or tailored link name) is present and lists every id.
- `"codelinks_comment"`: `{oneline_style: {start_sequence: str, field_split_char: str, needs_fields: list[dict]}}` — exact shape of `[codelinks.projects.<name>.analyse.oneline_comment_style]`.
- `"yaml_map"`: `{required_top_level_key: str, required_sub_keys: list[str], allowed_sub_keys: list[str]}`.
- `"json_obj"`: `{required_keys: list[str], allowed_unknown_keys: bool}`.

## Output

### Block mode

```json
{
  "valid": true,
  "errors": [],
  "parsed": [
    {
      "directive": "feat",
      "title": "CSV Export",
      "options": {"id": "FEAT_csv_export", "status": "draft", "source_doc": "features/csv.rst"},
      "body": "The system shall export sphinx-needs data to CSV files."
    }
  ],
  "recovery": {"stripped_text": null}
}
```

On `valid=false`, `parsed` is `null`. `errors` is a list of human-readable strings naming each violation with line numbers where possible.

### Graph mode

```json
{
  "valid": false,
  "errors": [],
  "needs_checked": 44,
  "violations": [
    {"need_id": "comp_req__auth_login",  "type": "comp_req", "missing_fields": ["tags"]},
    {"need_id": "comp_req__auth_logout", "type": "comp_req", "missing_fields": ["tags", "priority"]}
  ]
}
```

`valid` is `true` iff `violations` is empty. `needs_checked` counts every need read from `needs.json` (including ones whose type has no `required_metadata_fields` declared — they are still counted). `violations` is sorted by `need_id` ascending for deterministic fixture comparison. `errors` is reserved for structural problems (missing / unparseable input files) and is disjoint from `violations`: an error short-circuits with `valid: false`, empty `violations`, and `needs_checked: 0`.

## Recovery modes

Strict by default. One automatic recovery when `strip_fences=true`:

- If `output_text` starts with a triple-backtick fence (optionally with language hint) and ends with closing fence, strip fences and re-validate. If re-validation passes, return `valid=true` with `recovery.stripped_text` set. If it still fails, return `valid=false` with both original and stripped errors.

The validator never silently recovers from prose wrapping or option typos — those are always `valid=false`. The caller decides whether to re-dispatch the subagent or fail.

## Process

If `mode == "graph"`, skip directly to `## Graph mode` below. The steps in this section apply to block mode only.

### Step 1: Strip emit-header prefix if present

If `output_text` starts with `# emit=rst\n` or `# emit=codelinks_comment\n`, remove that line. Record what was stripped (for error messages).

### Step 2: Handle fence recovery (if `strip_fences=true`)

If `output_text` (after emit-header strip) matches `^```[a-z]*\n(.+?)\n```\s*$` (with `re.DOTALL`), capture the inner content. Validate the inner content as if it were the original. If it validates, return `valid=true` with `recovery.stripped_text` set. If it does not, fall through to validate the original and include both error sets.

### Step 3: Dispatch to schema-specific parser

Per `target_schema`, apply the parser:

- `rst_directive`: Stage 1 + Stage 2 regex from `pharaoh-req-from-code` `## Output schema`. Iterate blocks, enumerate options per block.
- `codelinks_comment`: invoke sphinx-codelinks' own `oneline_parser.parse_line()` per line.
- `yaml_map`: `yaml.safe_load`, check shape.
- `json_obj`: `json.loads`, check keys.

### Step 4: Apply schema-specific checks

Per `target_schema` and `schema_context`:

- `rst_directive`: directive equals `directive`; every `required_options` present; no option outside `allowed_options ∪ {required_options}`; if `parent_ids` given, `satisfies` value contains each; no non-blank content after last block.
- `codelinks_comment`: `parse_line()` returns a dict with every `needs_fields[].name` populated (or default applied).
- `yaml_map`: exactly one top-level key equal to `required_top_level_key`; sub-keys include every `required_sub_keys`; no sub-key outside `allowed_sub_keys ∪ required_sub_keys`.
- `json_obj`: every `required_keys` present; if `allowed_unknown_keys` is `false`, no unknown keys.

### Step 5: Return

```json
{"valid": true|false, "errors": [...], "parsed": ..., "recovery": {"stripped_text": ...}}
```

## Graph mode

Graph mode validates the tailored `required_metadata_fields` across every need in `needs.json`. It is the delegated check for the `metadata_fields_present` invariant in `pharaoh-quality-gate`.

### Process

1. **Load.** Parse `artefact_catalog_path` via `yaml.safe_load` into `{type: {required_metadata_fields: [str]}}`. Parse `needs_json_path` via `json.load` and extract the needs map (handle flat `needs` key or versioned `versions` shape). On either parse failure or missing file, return `{valid: false, errors: ["<message>"], needs_checked: 0, violations: []}`.
2. **Resolve per-type required-field lists.** For each type `T` present in `needs.json`, look up `catalog[T].required_metadata_fields`. Absent type or absent key → treat as `[]` (no check for that type; this is not an error). Empty list → no check for that type.
3. **Iterate needs.** For each need `N`:
   - Let `required = catalog[N.type].required_metadata_fields` (resolved per step 2; defaults to `[]`).
   - For each `field` in `required`, check the need dict. The field counts as **present and non-empty** when `field` is a key on the need AND the value is neither `None`, `""`, nor `[]`.
   - Collect all missing/empty field names for this need into `missing_fields`.
   - If `missing_fields` is non-empty, append `{need_id: N.id, type: N.type, missing_fields: <sorted>}` to `violations`.
4. **Aggregate.** Sort `violations` by `need_id` ascending for deterministic output. Set `valid = len(violations) == 0`.

### Detection rule (reference)

```python
import json, yaml

catalog = yaml.safe_load(open(artefact_catalog_path)) or {}
nj      = json.load(open(needs_json_path))
needs   = nj.get("needs") or next(iter(nj.get("versions", {}).values()), {}).get("needs", {})

violations = []
for nid, n in needs.items():
    t        = n.get("type")
    required = (catalog.get(t) or {}).get("required_metadata_fields") or []
    missing  = [f for f in required
                if n.get(f) in (None, "", []) or f not in n]
    if missing:
        violations.append({"need_id": nid, "type": t, "missing_fields": sorted(missing)})

violations.sort(key=lambda v: v["need_id"])
result = {
    "valid": len(violations) == 0,
    "errors": [],
    "needs_checked": len(needs),
    "violations": violations,
}
```

### Tailoring extension point

The full policy lives in `artefact-catalog.yaml`. Each type declares its own `required_metadata_fields` independently:

```yaml
comp_req:
  required_metadata_fields: [tags, priority]
feat:
  required_metadata_fields: [tags]
tc:
  required_metadata_fields: []           # explicitly no check
gd_req:
  # required_metadata_fields omitted     # treated as empty, no check
```

No hardcoded field names in the base skill. Projects that do not care about metadata completeness either set empty lists or omit the key — either way, graph mode returns `valid: true` with no violations.

## Failure modes

Block mode:
- `output_text` empty → `valid=false`, errors=["empty output"].
- `target_schema` unknown → FAIL (caller error).
- `schema_context` missing required fields → FAIL (caller error).
- Parser throws (malformed YAML/JSON/RST) → `valid=false`, errors=["parser exception: <message>"].

Graph mode:
- `needs_json_path` or `artefact_catalog_path` missing or unparseable → `valid=false`, `errors` names the offending path, `needs_checked=0`, empty `violations`.
- Empty corpus (`needs` is `{}`) → `valid=true`, `needs_checked=0`, empty `violations` (vacuously true).
- `mode` value not in `{"block", "graph"}` → FAIL (caller error).

## Non-goals

- No side effects — never writes files, never dispatches subagents, never retries.
- No semantic validation beyond option-name/key-name presence — e.g. does not check whether `parent_feat_id` values exist in the project; that is a downstream concern.
- No repair — output is either valid, fence-strippable, or rejected.
- Graph mode does NOT validate link-target resolution, id convention, or status lifecycle — those live in `pharaoh-link-completeness-check`, `pharaoh-id-convention-check`, and `pharaoh-status-lifecycle-check` respectively. Graph mode only checks tailored required-metadata-field presence, keeping the atom's single responsibility intact.

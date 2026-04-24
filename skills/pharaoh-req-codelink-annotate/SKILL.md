---
name: pharaoh-req-codelink-annotate
description: Use when a requirement has been drafted (either as an RST block by `pharaoh-req-from-code` or implicitly) and you need to insert a one-line comment into the source file that carries the trace. Two modes — `codelinks` (sphinx-codelinks-compatible multi-field `@ title, id, type, [links]` form; the comment IS the need) and `backref` (minimal `@req ID: title` pointer back to an RST-hosted need). Mode is tailored via `ubproject.toml` / `pharaoh.toml`, not hardcoded.
---

# pharaoh-req-codelink-annotate

## When to use

Invoke when you want a source file to carry a machine- and human-readable reference to a requirement. The resulting comment either:

- **`codelinks` mode** — contains the full need definition in sphinx-codelinks one-line format (e.g. `# @ Write CSV header row, CREQ_csv_export_01, comp_req, [FEAT_csv_export]`). When the project builds Sphinx with `sphinx_codelinks` loaded, this comment becomes an actual need directive at render time. The comment IS the source of truth.
- **`backref` mode** — contains only a pointer to a need defined elsewhere (e.g. `# @req CREQ_csv_export_01: Write CSV header row`). The RST block (e.g. from `pharaoh-req-from-code`) is the source of truth; the comment exists for grep/IDE navigation only.

Mode is not a per-call preference — it is a project-level decision baked into `ubproject.toml` / `pharaoh.toml` (see Tailoring awareness). The caller may override per invocation, but the default MUST come from tailoring so that the whole codebase stays consistent.

Do NOT use to generate the requirement's text (that is `pharaoh-req-from-code` with appropriate `emit` mode). Do NOT use to delete or update comments after the fact — this skill only inserts, per atomicity.

## Tailoring awareness — mode resolution

The skill resolves `mode` in this order:

1. Input `mode_override` parameter (per-call, highest precedence).
2. `pharaoh.toml` → `[pharaoh.codelink_comments].mode` (explicit project choice).
3. Auto-detect: if `ubproject.toml` contains `[codelinks.projects.*]` (i.e. sphinx-codelinks is in use) → `"codelinks"`; otherwise `"backref"`.
4. Fallback: `"backref"` (conservative — a dumb grep-able pointer is safe even if the project later adopts sphinx-codelinks).

### `codelinks` mode configuration

Comes from `ubproject.toml` under `[codelinks.projects.<name>.analyse.oneline_comment_style]` — exactly the table sphinx-codelinks itself reads. The skill does NOT re-invent this schema; it reads the same `start_sequence`, `end_sequence`, `field_split_char`, and `needs_fields` that sphinx-codelinks will use to parse the comment at build time. This guarantees round-trip safety: what this skill writes, sphinx-codelinks reads.

The caller must indicate which codelinks project the file belongs to, via input `codelinks_project_name`. If omitted, the skill tries to infer from `file_path` + each project's `source_discover.src_dir`; if exactly one project matches, use it; if zero or multiple match → FAIL asking the caller to be explicit. This keeps the skill atomic (no hidden "which project" guessing) while staying ergonomic.

### `backref` mode configuration

Comes from `pharaoh.toml`:

```toml
[pharaoh.codelink_comments]
mode = "backref"
prefix = "@req"                       # marker for grep
format = "{prefix} {id}: {title}"     # template
```

If `pharaoh.codelink_comments` is absent, defaults: `prefix = "@req"`, `format = "{prefix} {id}: {title}"`.

### `check → propose → confirm`

If `on_missing_config == "prompt"` (default) AND no tailoring is found (neither `pharaoh.codelink_comments` nor `[codelinks.projects.*]`), the skill does NOT silent-default. It returns a structured proposal object:

```json
{
  "status": "needs_confirmation",
  "proposal": {
    "mode": "backref",
    "rationale": "No [codelinks.projects.*] table in ubproject.toml — project does not appear to use sphinx-codelinks. Proposing minimal backref mode.",
    "tailoring_patch": {
      "target_file": "pharaoh.toml",
      "section": "[pharaoh.codelink_comments]",
      "patch": {"mode": "backref", "prefix": "@req", "format": "{prefix} {id}: {title}"}
    }
  }
}
```

The caller confirms (humans or an outer LLM), the tailoring gets written (typically via `pharaoh-tailor-fill`), and the skill is re-invoked — now finding the config and proceeding silently with `on_missing_config="use_default"` semantics.

### Language-to-comment-syntax mapping

Derived from file extension (both modes):

| Extension | Prefix |
|---|---|
| `.py`, `.rb`, `.sh`, `.toml`, `.yaml`, `.yml` | `#` |
| `.c`, `.cpp`, `.cxx`, `.cc`, `.h`, `.hpp`, `.hxx`, `.ts`, `.tsx`, `.js`, `.jsx`, `.rs`, `.go`, `.java`, `.kt`, `.swift`, `.scala`, `.groovy`, `.dart` | `//` |
| `.sql`, `.hs`, `.lua`, `.ada` | `--` |

Unknown extension → FAIL rather than guess.

## Atomicity

- (a) Indivisible — one (req_id, file_path, anchor) triple in → one comment line inserted. No multi-req batching, no req text modification, no RST file modification.
- (b) Input: `{req_id: str, req_title: str, req_type: str, file_path: str, anchor: AnchorSpec, project_root: str, parent_links?: list[str], mode_override?: "codelinks"|"backref", codelinks_project_name?: str, on_missing_config?: "fail"|"prompt"|"use_default", dry_run?: bool}`. Output: JSON `{mode_used: "codelinks"|"backref", inserted_line: int, inserted_text: str, file_modified: bool}`. On `dry_run=true` → `file_modified=false`, no write. On `on_missing_config="prompt"` with no tailoring → `{status: "needs_confirmation", proposal: ...}` (see Tailoring awareness).
- (c) Reward: two deterministic fixtures, one per mode.

  **Fixture A — `codelinks` mode** (project tailored with `[codelinks.projects.demo.analyse.oneline_comment_style]` matching sphinx-codelinks defaults: `start_sequence="@"`, `field_split_char=","`, `needs_fields=[title, id, type, links]`). 20-line `.py` file, known anchor, known (req_id, req_title, req_type, parent_links=["FEAT_X"]). Scorer:
  1. File is still syntactically valid Python.
  2. Exactly one line added.
  3. Inserted line starts with `# @ ` (comment prefix + start_sequence + space).
  4. Parsing the inserted line with sphinx-codelinks' own oneline parser (or a faithful reimplementation) yields a need with `title==req_title`, `id==req_id`, `type==req_type`, `links==parent_links`.
  5. `mode_used == "codelinks"` in output.
  6. Idempotent re-run: second invocation detects `req_id` substring, no-op, `file_modified=false`.

  **Fixture B — `backref` mode** (project without `[codelinks.*]` and without `[pharaoh.codelink_comments]`, `on_missing_config="use_default"`). Same file shape. Scorer:
  1. File is still syntactically valid Python.
  2. Exactly one line added.
  3. Inserted line starts with `# @req ` (default backref prefix).
  4. Inserted line contains both `req_id` and `req_title` as substrings.
  5. `mode_used == "backref"` in output.
  6. Idempotent re-run: no-op.

  **Fixture C — prompt mode** (no tailoring, `on_missing_config="prompt"`). Scorer:
  1. Output has `status == "needs_confirmation"`.
  2. Output has `proposal.mode == "backref"` (conservative default).
  3. Output has `proposal.tailoring_patch` pointing at `pharaoh.toml`.
  4. File was NOT modified.

  Pass = all checks in all three fixtures.
- (d) Reusable: any source tree in any supported language; bidirectional trace for reverse-engineered reqs; IDE-navigable "where is this req implemented" queries via grep.
- (e) Composable: strictly one phase (source mutation, one comment). Never modifies RST, never calls `pharaoh-req-from-code` or other skills. A plan emitted by `pharaoh-write-plan` MAY include a foreach task over req-emission outputs that dispatches this skill per req, but this skill itself does not orchestrate.

## Input

- `req_id`: the requirement's sphinx-needs ID (e.g. `"CREQ_csv_export_01"`).
- `req_title`: the requirement's short title (e.g. `"Write CSV header row"`).
- `req_type`: the requirement's directive name (e.g. `"comp_req"`, `"impl"`). In `codelinks` mode used for the `type` field. In `backref` mode used only if the tailored `format` template includes `{type}`.
- `file_path`: absolute path to the source file to annotate.
- `anchor`: `AnchorSpec` — one of:
  - `{type: "top_of_file"}` — insert after shebang/encoding lines but before any other content.
  - `{type: "before_symbol", symbol: "<name>"}` — insert immediately before the line where `<name>` is defined. Regex-based detection, not AST-level.
  - `{type: "before_line", line: <n>}` — insert before line `<n>` (1-indexed).
- `project_root`: absolute path to the consumer project's root. Used to locate `ubproject.toml` (for `codelinks` mode config) and `pharaoh.toml` (for `backref` mode config and mode selection).
- `parent_links` (optional): list of parent IDs (e.g. `["FEAT_csv_export"]`). In `codelinks` mode used for the `links` field verbatim. In `backref` mode used only if the tailored `format` template includes `{parent_links}`.
- `mode_override` (optional): `"codelinks"` or `"backref"`. Forces mode for this call. If omitted, resolution follows the order in Tailoring awareness.
- `codelinks_project_name` (optional): which entry under `[codelinks.projects.*]` in `ubproject.toml` this file belongs to. Required when multiple projects are defined and their `source_discover.src_dir` values would both match `file_path`. Ignored in `backref` mode.
- `on_missing_config` (optional): `"fail" | "prompt" | "use_default"`. Default `"prompt"`. Determines behavior when tailoring is missing (see Tailoring awareness).
- `dry_run` (optional): if `true`, skill returns what WOULD be written without touching the file. Default `false`.

## Output

A single JSON object, one of three shapes:

**Success shape (file modified):**

```json
{
  "mode_used": "backref",
  "inserted_line": 15,
  "inserted_text": "# @req CREQ_csv_export_01: Write CSV header row",
  "file_modified": true
}
```

**Idempotent re-run (comment already present):**

```json
{
  "mode_used": "backref",
  "inserted_line": 15,
  "inserted_text": "# @req CREQ_csv_export_01: Write CSV header row",
  "file_modified": false
}
```

**Needs-confirmation (no tailoring, `on_missing_config="prompt"`):**

```json
{
  "status": "needs_confirmation",
  "proposal": {
    "mode": "backref",
    "rationale": "No [codelinks.projects.*] table in ubproject.toml — proposing minimal backref mode.",
    "tailoring_patch": {
      "target_file": "pharaoh.toml",
      "section": "[pharaoh.codelink_comments]",
      "patch": {"mode": "backref", "prefix": "@req", "format": "{prefix} {id}: {title}"}
    }
  }
}
```

On `dry_run=true`, `file_modified` is always `false`.

## Output schema

Output must parse as JSON via `json.loads`. Validator checks one of two shapes:

**Success shape:**
- Required keys: `mode_used` (one of `"codelinks"`, `"backref"`), `inserted_line` (int ≥ 1), `inserted_text` (non-empty str), `file_modified` (bool).
- Unknown keys are permitted and surface as a warning, not a rejection, to allow forward-compatible evolution.

**Needs-confirmation shape:**
- Required keys: `status == "needs_confirmation"`, `proposal` (mapping). See `## Tailoring awareness` for proposal details.
- Mutually exclusive with the success shape (a response has one or the other, never both).

## Process

### Step 1: Resolve mode

Resolve `mode` per the Tailoring awareness order:
1. `mode_override` → use directly.
2. `pharaoh.toml [pharaoh.codelink_comments].mode` → use.
3. `ubproject.toml` has any `[codelinks.projects.*]` table → `"codelinks"`.
4. Fallback → `"backref"`.

If resolution step 2 and 3 both yield nothing AND `on_missing_config == "prompt"` → emit the `needs_confirmation` proposal object described in Tailoring awareness and return without modifying the file.

If `on_missing_config == "fail"` and no config → FAIL.

If `on_missing_config == "use_default"` and no config → proceed with `"backref"` silently.

### Step 2a: Format the comment — `codelinks` mode

1. Determine the codelinks project: use `codelinks_project_name` if provided; else infer by matching `file_path` against each `[codelinks.projects.*].source_discover.src_dir`. If exactly one matches, use that project. If zero or multiple → FAIL.
2. Read `[codelinks.projects.<name>.analyse.oneline_comment_style]` from `ubproject.toml`:
   - `start_sequence` (e.g. `"@"`)
   - `end_sequence` (optional; default empty)
   - `field_split_char` (e.g. `","`)
   - `needs_fields`: ordered list of `{name, type?, default?}` entries.
3. Build the field values in declared order:
   - For each field, pick the value from the mapping: `title`=`req_title`, `id`=`req_id`, `type`=`req_type`, `links`=`parent_links` (rendered as `[a, b, c]` per sphinx-codelinks list-of-strings syntax).
   - If a declared field has no matching value AND has a `default` → omit (sphinx-codelinks will fill it). Else FAIL naming the missing field.
   - Escape `field_split_char` and `[`/`]` characters in string values per sphinx-codelinks escaping rules (backslash prefix).
4. Join fields with `" " + field_split_char + " "` (a space, separator, space — matching sphinx-codelinks' own formatting).
5. Prepend `start_sequence + " "` (e.g. `"@ "`).
6. Append `end_sequence` if non-empty.
7. The result is the comment text body. Example: `"@ Write CSV header row, CREQ_csv_export_01, comp_req, [FEAT_csv_export]"`.

### Step 2b: Format the comment — `backref` mode

Read `<project_root>/pharaoh.toml` if present. Extract `[pharaoh.codelink_comments]`:
- `prefix` (default `"@req"`)
- `format` (default `"{prefix} {id}: {title}"`)

Substitute placeholders:
- `{prefix}` → the prefix value
- `{id}` → `req_id`
- `{title}` → `req_title`
- `{type}` → `req_type`
- `{parent_links}` → `", ".join(parent_links)` or empty string if not provided

### Step 3: Resolve comment syntax from file extension

Map file extension → comment prefix:

| Extension | Prefix |
|---|---|
| `.py`, `.rb`, `.sh`, `.toml`, `.yaml`, `.yml` | `#` |
| `.c`, `.cpp`, `.cxx`, `.cc`, `.h`, `.hpp`, `.hxx`, `.ts`, `.tsx`, `.js`, `.jsx`, `.rs`, `.go`, `.java`, `.kt`, `.swift`, `.scala`, `.groovy`, `.dart` | `//` |
| `.sql`, `.hs`, `.lua`, `.ada` | `--` |

Unknown extension → FAIL: `"Cannot determine comment syntax for extension <ext>. Add the extension to the mapping or pass a file with a known extension."`.

The inserted line is: `<comment_prefix> <formatted_text>`.

### Step 4: Read the file

Read `file_path`. Split into lines (preserve trailing newline state for round-trip).

### Step 5: Idempotency check

Scan every line for `req_id` as a substring. If any line contains it, the comment is already present (or a different reference to the same req exists). Return without modifying the file:

```json
{"inserted_line": <matched_line_index>, "inserted_text": "<matched_line>", "file_modified": false}
```

This is the idempotency guarantee from reward check #6. Do NOT re-insert, do NOT duplicate, do NOT update a stale title (if the title changed, the human is responsible for deleting the old line; auto-update risks corrupting hand-edited comments).

### Step 6: Resolve anchor to a line index

- `top_of_file`: skip shebang (`#!`) and encoding lines (`# -*- coding: ... -*-`, `# coding: ...`), stop at the first content line. Insert immediately before it.
- `before_symbol`: regex-scan for the symbol's declaration line. Language-specific patterns:
  - Python: `^\s*(def|class|async\s+def)\s+<name>\b`
  - JS/TS: `^\s*(function|class|const|let|var)\s+<name>\b`, also `^\s*<name>\s*(?::|=)` for object-method shorthand
  - Rust: `^\s*(pub\s+)?(fn|struct|enum|trait|impl)\s+<name>\b`
  - Go: `^\s*func\s+(\([^)]*\)\s+)?<name>\b`, also `^\s*(type\s+<name>\b|var\s+<name>\b)`
  - C/C++: `^\s*[\w:*&<>\s]+\s+<name>\s*\(` (function) or `^\s*(class|struct|enum)\s+<name>\b` (type)
  
  If multiple matches, warn and use the first. If zero matches, FAIL: `"Symbol <name> not found in <file_path>."`.
- `before_line`: validate `1 <= line <= len(lines) + 1`. FAIL if out of range.

### Step 7: Insert the comment

If `dry_run=true`, return without writing:

```json
{"inserted_line": <resolved_line>, "inserted_text": "<formatted_comment>", "file_modified": false}
```

Otherwise, insert the comment line at the resolved index. Preserve indentation — the comment inherits the indentation of the line it precedes (so it stays at the correct nesting level for `before_symbol` anchors).

Write the file back. Preserve original EOL convention (LF vs CRLF) and final-newline state.

### Step 8: Return

Return the JSON object per the Output shape with `file_modified=true`.

## Failure modes

- `file_path` not readable → FAIL: `"file not readable: <path>"`.
- Unknown extension → FAIL per Step 2.
- Symbol not found for `before_symbol` anchor → FAIL per Step 5.
- Line out of range for `before_line` anchor → FAIL per Step 5.
- File is in `.git/`, `node_modules/`, `__pycache__/`, or a build output directory (detected by path segment) → FAIL: `"Refusing to annotate generated/vendored file: <path>"`. This protects against accidental writes into machine-generated code.

## Non-goals

- No AST-level insertion — regex is deliberately simple to keep the skill language-agnostic. Callers who need AST-precise placement should use a language-specific tool and pass `before_line` with the exact line number.
- No multi-comment insertion in one call — this skill is atomic per (req, file, anchor). Callers who need N comments make N calls.
- No cross-file traceability validation — a separate skill (`pharaoh-codelink-validate`, not yet implemented) will scan for orphan back-references whose req no longer exists.
- No removal — if a req is deleted, the comment stays until a human or a dedicated cleanup skill removes it. This skill only inserts.

## Composition

The typical flow:

1. A plan emitted by `pharaoh-write-plan` includes a foreach task over req-from-code outputs; `pharaoh-execute-plan` dispatches N `pharaoh-req-from-code` instances that generate `comp_req` blocks.
2. Caller (human or the same plan) reviews and accepts the reqs.
3. A downstream foreach task in the same plan (typically `id: codelink_annotate`) dispatches this skill per accepted req with:
   - `req_id`, `req_title`, `req_type` from the RST block
   - `file_path` = the source file the req was derived from (available from the `req-from-code:<filename>` `reporter_id` used by the upstream task)
   - `anchor` = `{type: "top_of_file"}` for coarse placement, or `{type: "before_symbol", symbol: <primary_symbol>}` when the req is clearly about a specific function/class.

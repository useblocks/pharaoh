---
name: pharaoh-feat-file-map
description: Use when mapping one feature (already emitted as an RST directive) to the source files that implement it. Reads the source tree, returns a YAML entry `{feat_id: {files: [...], rationale: "..."}}`. Does NOT read docs. Does NOT emit reqs. Does NOT create or modify source files.
---

# pharaoh-feat-file-map

## When to use

Invoke after `pharaoh-feat-draft-from-docs` has emitted one or more feature directives, when you need to know which source files implement each feature. The emitted mapping feeds downstream `pharaoh-req-from-code` tasks (one invocation per file, with `parent_feat_ids` set from this mapping), producing `comp_req` directives that link back to the parent feature via `:satisfies:`.

One invocation handles exactly one feature. To map N features, a plan emitted by `pharaoh-write-plan` uses a `foreach` task over feats to dispatch N instances concurrently.

Do NOT use to draft features (that is `pharaoh-feat-draft-from-docs`). Do NOT use to emit reqs (that is `pharaoh-req-from-code`). Do NOT modify source files (that is a future bidirectional-trace skill).

## Tailoring awareness

This skill does not emit RST directives, so it is type-agnostic. It does, however, respect the consumer project's source layout: if `pharaoh.toml` or `ubproject.toml` declares a `[pharaoh.codelinks]` section or a sphinx-codelinks `source_discover.src_dir`, the skill uses that as the default `src_root`. Otherwise the caller must pass `src_root` explicitly.

## Atomicity

- (a) Indivisible — one feature in → one YAML entry out. No RST emit. No other feature analysis. One artefact × one phase.
- (b) Input: `{feat_id: str, feat_title: str, feat_body: str, src_root: str, file_glob?: str, exclude_glob?: list[str], papyrus_workspace?: str, reporter_id: str}`. Output: a single YAML object in FLAT shape `{feat_id: <str>, files: [<relative_path>, ...], rationale: "<one-sentence explanation>", entry_point?: <mapping>, shared_with?: [<feat_id>]}`. No wrapping prose, no outer `{<feat_id>: ...}` key — the `feat_id` lives as a sibling scalar alongside `files` and `rationale` so downstream aggregation over foreach results is a trivial list-of-mappings, not a merge of single-key mappings.
- (c) Reward: deterministic fixture — a 5-file source tree where 3 files clearly implement feature "FEAT_csv_export" (e.g. `csv/export.py`, `csv/writer.py`, `commands/csv.py`) and 2 are unrelated (`jama/client.py`, `reqif/parser.py`). After skill runs, scorer checks:
  1. Output is valid YAML parseable by PyYAML.
  2. Output has top-level keys including `feat_id` (equal to input `feat_id`), `files` (list), `rationale` (string).
  3. No other top-level keys are present beyond the optional `entry_point` and `shared_with`.
  4. Every path in `files` exists under `src_root`.
  5. Precision: of emitted files, ≥80% are in the fixture's ground-truth positive set.
  6. Recall: of the fixture's ground-truth positive files, ≥60% are in emitted `files`.

  Precision and recall targets are deliberately asymmetric — we accept more false positives than false negatives because downstream `pharaoh-req-from-code` can tolerate an extra file (just produces an extra req the human can delete), but missing a file means a behavior gets no requirement at all.
- (d) Reusable: any reverse-engineering workflow; impact analysis ("which files does this feature touch?"); rough component boundary detection.
- (e) Composable: one feature per call. A plan emitted by `pharaoh-write-plan` dispatches N instances via `foreach` when multiple feats exist. This skill never calls `pharaoh-feat-draft-from-docs` or `pharaoh-req-from-code`.

## Input

- `feat_id`: the feature's sphinx-needs ID (e.g. `"FEAT_csv_export"` or `"feat__csv_export"`). Used verbatim as the YAML key.
- `feat_title`: the feature's short title (e.g. `"CSV Export"`). Used for semantic reasoning about file relevance.
- `feat_body`: the feature's one-sentence statement (e.g. `"The system shall export needs to CSV files."`). Used for semantic reasoning.
- `src_root`: absolute path to the source tree to scan. All emitted file paths are relative to this root.
- `file_glob` (optional): glob pattern for candidate files. Default: `"**/*"` minus common excludes (see `exclude_glob`). Callers for a Python project may pass `"**/*.py"`; for a polyglot project, a combined pattern.
- `exclude_glob` (optional): list of glob patterns to exclude. Default: `["**/__pycache__/**", "**/.git/**", "**/node_modules/**", "**/*.pyc", "**/tests/**", "**/test_*.py", "**/*_test.py"]`. Tests are excluded by default because they describe verification, not implementation; a separate skill can map tests to features if needed.
- `papyrus_workspace` (optional): path to `.papyrus/` directory. If provided, the skill queries for prior knowledge about which files implement which concepts (enables cross-run consistency).
- `reporter_id`: short identifier for this agent (e.g. `feat-file-map:FEAT_csv_export`).

## Output

A single YAML document, no prose wrapper:

```yaml
feat_id: FEAT_csv_export
files:
  - csv/export.py
  - csv/writer.py
  - commands/csv.py
rationale: "Export pipeline: export.py orchestrates, writer.py serializes rows, commands/csv.py registers the CLI entrypoint."
```

Top-level keys: `feat_id` (equal to input), `files`, `rationale`. Optional top-level keys:

- `shared_with: list[feat_id]` — populated by the orchestrator when the same file serves multiple features (see below).
- `entry_point: {file: str, symbol: str}` — names the file + symbol where feature flow begins (typically a CLI command, HTTP route, test entry, event handler). Downstream `pharaoh-feat-flow-extract` reads this to know where to start the call-chain walk. Leave absent when no single entry point applies (e.g. the feature is a pure data model with no orchestrating function).

`files` is a list of strings (each a path relative to `src_root`) and `rationale` is a one-sentence string explaining why these files were chosen.

Example with entry_point (recommended when one clearly exists):

```yaml
feat_id: FEAT_csv_export
files:
  - csv/export.py
  - csv/writer.py
  - commands/csv.py
rationale: "Export pipeline from CLI through the writer."
entry_point:
  file: commands/csv.py
  symbol: export
```

When a file implements behavior across multiple features (e.g. `commands/reqif.py` serves both ReqIF import and export), the `to_files_flat` helper in a plan emitted by `pharaoh-write-plan` detects this by seeing the same path appear under multiple feat entries (each entry a flat mapping produced by one `foreach` instance of this skill). It denormalises so the file appears once with `parents: [<feat_ids>]` listing all parents. Example (two instances from different foreach iterations):

```yaml
# instance 1 (feat: FEAT_reqif_export)
feat_id: FEAT_reqif_export
files:
  - reqif/needs2reqif.py
  - commands/reqif.py
rationale: "..."

# instance 2 (feat: FEAT_reqif_import)
feat_id: FEAT_reqif_import
files:
  - reqif/reqif2needs.py
  - commands/reqif.py   # shared with FEAT_reqif_export
rationale: "..."
```

This atomic skill emits one entry at a time; cross-entry consolidation happens in the plan via `to_files_flat`, not in this skill.

If no files match, emit:

```yaml
feat_id: <input feat_id>
files: []
rationale: "No source files matched this feature — check whether the feature is implemented in src_root or whether file_glob/exclude_glob are too restrictive."
```

Empty `files` is a valid output; the orchestrator decides whether to surface it as a warning.

## Output schema

Output must parse as a YAML document via `yaml.safe_load`. Validator checks:
1. Parsed root is a mapping with required keys `feat_id` (string equal to input `feat_id`), `files` (list of strings), `rationale` (non-empty string).
2. Optional top-level keys `shared_with` (list of strings) and `entry_point` (mapping with required `file: str` and `symbol: str`) are permitted; no other top-level keys accepted.
3. Every entry in `files` is a non-empty string.
4. `rationale` is a non-empty string.

## Process

### Step 1: Query Papyrus for prior file associations (if workspace provided)

Query `pharaoh-context-gather` with `feat_title + " " + feat_body` against `papyrus_workspace`. If any prior memories link this feature (or a canonically-equivalent one) to specific files, bias toward those files in Step 3. If not, proceed.

### Step 2: Enumerate candidate files

Apply `file_glob` under `src_root`, then filter out everything matching `exclude_glob`. Read the resulting list of candidate files.

### Step 3: Score each candidate for relevance to the feature

For each candidate, read the first ~200 lines (or full file if smaller). Reason about relevance:

- Strong positive signals: file name matches feature keywords (e.g. `csv_export.py` for CSV export); top-level function/class names use feature keywords; docstrings mention the feature's capability.
- Weak positive signals: imports from modules whose names match feature keywords; file is in a subdirectory whose name matches feature keywords.
- Negative signals: file name matches a different feature's keywords; file is clearly a helper/utility imported by many unrelated modules.

Do NOT use file size as a signal. Do NOT use modification date as a signal. Do NOT follow imports transitively (that explodes scope).

Assign each candidate an internal relevance score (high / medium / low / none). Emit all `high` and `medium` files. Drop `low` and `none`.

### Step 4: Write rationale

One sentence, ≤ 25 words, explaining the emitted file set. Example: `"reqif/reqif2needs.py parses XML, reqif/section.py handles section groups, commands/reqif.py wires the CLI."`

Do NOT list every file in the rationale (that duplicates `files`). Instead describe the ROLE each file plays.

### Step 4b: Identify entry_point (optional)

After selecting the emitted files, identify the "entry point" — the file + symbol where user-facing flow begins. Heuristics, in order of preference:

1. File in a directory named `commands/`, `cli/`, `api/`, `routes/`, `handlers/`, or `entrypoints/`.
2. File whose primary symbol name matches feat title tokens (case-insensitive substring).
3. File with a decorator-style entry marker (`@app.command()`, `@click.command()`, `@router.get()`, `@fastapi.*`).

If exactly one candidate matches, emit `entry_point`. If multiple match, pick the one closest to the feat title tokens. If zero match, OMIT `entry_point` entirely (downstream skill detects absence and skips flow extraction).

Do NOT invent an entry_point when the feat is a data model, a shared utility, or a configuration artefact with no orchestrating function.

### Step 5: Return YAML

Return the YAML object. No prose before or after.

## Failure modes

- `src_root` not readable → FAIL: "src_root unreadable: <path>".
- `feat_id` missing or not a string → FAIL: "feat_id must be a non-empty string".
- Zero candidate files after glob filtering → emit empty `files` with explanatory `rationale`, do NOT fail.
- `pharaoh-context-gather` errors → log and proceed without Papyrus bias.

## Composition

A plan emitted by `pharaoh-write-plan` calls `pharaoh-feat-draft-from-docs` once, then uses a `foreach` task to dispatch one `pharaoh-feat-file-map` per emitted feature in parallel. Merging / denormalisation to a flat file list happens in the plan via the `to_files_flat` helper — this skill never reads or writes a merged file.

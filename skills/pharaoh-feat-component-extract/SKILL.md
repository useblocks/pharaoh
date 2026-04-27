---
name: pharaoh-feat-component-extract
description: Use when reverse-engineering a feat and you need to derive a component composition diagram automatically from the feat + its source files. Walks import edges between the listed files and emits a Mermaid or PlantUML diagram whose output shape is compatible with pharaoh-component-diagram-draft. Does NOT hand-author nodes or edges; extraction is rule-based.
---

# pharaoh-feat-component-extract

## When to use

Invoke after `pharaoh-feat-file-map` has produced a `{feat_id, files}` mapping, when you want a static architecture view of the feature showing which modules/classes compose it and how they depend on each other. The diagram output shape matches `pharaoh-component-diagram-draft` so downstream tooling (sphinx-needs rendering, diff review) treats auto-extracted diagrams identically to hand-authored ones.

Do NOT use to draft a diagram from scratch when you already have explicit node+edge data — that is `pharaoh-component-diagram-draft`. Do NOT use to extract runtime flow — that is `pharaoh-feat-flow-extract`.

## Tailoring awareness

Shared tailoring rules: see `shared/diagram-tailoring.md`. Reads `[pharaoh.diagrams]` and `[pharaoh.diagrams.component]` from the consumer project's `pharaoh.toml` for renderer choice and styling. Respects `on_missing_config` per the shared `check → propose → confirm` pattern.

Safe-label rules: see `shared/diagram-safe-labels.md`. Node IDs derived from file paths MUST be aliased (path characters `/` and `.` are invalid in Mermaid / PlantUML identifier positions). Edge labels MUST be sanitised — call-labels like `foo(arg1; arg2)` become `foo(arg1, arg2)` before emit. A parse failure in the emitted block is invisible under `sphinx-build` and surfaces only at browser render time; `pharaoh-diagram-lint` (run as part of `pharaoh-quality-gate`) is the second guard.

## Atomicity

- (a) Indivisible — one feat + one file list in → one diagram RST block out. No multi-feat bundling. No mutation of source files. No req emission.
- (b) Input: `{feat_id: str, feat_title: str, files: list[str], project_root: str, src_root: str, renderer_override?: "mermaid"|"plantuml", include_external?: bool, on_missing_config?: "fail"|"prompt"|"use_default", papyrus_workspace?: str, reporter_id: str}`. Output: one RST directive block (`.. mermaid::` or `.. uml::`) with caption `<feat_id> — component composition`. No surrounding prose.
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-feat-component-extract/`:
  - `input_feat.yaml` declares `feat_id: FEAT_csv_export`, `feat_title: "CSV Export"`, `files: [csv/export.py, csv/writer.py, commands/csv.py]`.
  - `input_files/` contains three Python files with explicit imports: `commands/csv.py` imports `from csv.export import run_export`; `csv/export.py` imports `from csv.writer import CSVWriter`; `csv/writer.py` has no project-internal imports.
  - Expected diagram at `expected_diagram.rst` has 3 nodes (one per file), 2 directed edges (`commands/csv.py → csv/export.py`, `csv/export.py → csv/writer.py`), no external nodes.
  
  Scorer:
  1. Output starts with the renderer directive.
  2. All 3 nodes appear by label.
  3. Both directed edges render with correct arrow syntax.
  4. With default `include_external=false`, no external imports (e.g. `typer`, `pathlib`, `csv`) appear as nodes.
  5. With `include_external=true`, external imports render as ghost nodes (dashed outline, muted color, `<<external>>` stereotype).
  6. Output matches `pharaoh-component-diagram-draft` output shape (same directive, same caption format, same node/edge syntax).

  Pass = all 6.
- (d) Reusable for any language whose import graph the extractor supports. Python initial target; regex-based import detection so adding Rust/TypeScript is a configuration table entry, not a rewrite.
- (e) Composable: one feat per call. A plan emitted by `pharaoh-write-plan` may include a `foreach` task over feats that dispatches N instances (one per feat) in parallel via `pharaoh-execute-plan`. This skill never invokes other skills.

## Input

- `feat_id`: the feature's sphinx-needs ID, used as the diagram caption prefix.
- `feat_title`: human-readable title, shown in caption.
- `files`: list of source file paths relative to `src_root`. These become the diagram's in-scope nodes.
- `project_root`: absolute path, for `pharaoh.toml` tailoring lookup.
- `src_root`: absolute path, the import-graph resolution root. `files[*]` resolve as `<src_root>/<file>`.
- `renderer_override` (optional): per shared doc.
- `include_external` (optional): if `true`, imports that resolve outside `files` but inside `src_root` become ghost nodes. Imports resolving outside `src_root` entirely (stdlib, third-party) are ignored regardless. Default `false`.
- `on_missing_config` (optional): per shared doc. Default `"prompt"`.
- `papyrus_workspace` (optional): for consistent node labeling with other skills that reference the same files.
- `reporter_id`: short agent identifier.

## Output

**Mermaid (default):**
```rst
.. mermaid::
   :caption: FEAT_csv_export — component composition

   graph TD
       commands_csv[commands/csv.py<br/>run_export]
       csv_export[csv/export.py<br/>run_export]
       csv_writer[csv/writer.py<br/>CSVWriter]
       commands_csv --> csv_export
       csv_export --> csv_writer
```

Node IDs (left-hand side of the bracket) are sanitized forms of the file path (replace `/` and `.` with `_`). Node labels show the file path plus the primary symbol (largest top-level def/class, or the one whose name matches feat title tokens).

**PlantUML:**
```rst
.. uml::
   :caption: FEAT_csv_export — component composition

   @startuml
   component "commands/csv.py\n(run_export)" as commands_csv
   component "csv/export.py\n(run_export)" as csv_export
   component "csv/writer.py\n(CSVWriter)" as csv_writer
   commands_csv --> csv_export
   csv_export --> csv_writer
   @enduml
```

## Process

### Step 1: Enumerate nodes

For each file in `files`, read via absolute path (`<src_root>/<file>`). Parse top-level symbol declarations:

- Python: `^class <Name>`, `^def <Name>`, `^async def <Name>`.
- Rust: `^(pub )?(fn|struct|enum|trait|impl) <Name>`.
- JS/TS: `^(export )?(function|class|const|let|var) <Name>`.
- Go: `^func (<Receiver>) <Name>` / `^type <Name>`.

Pick the primary symbol per file: longest body OR name matching `feat_title` tokens (case-insensitive substring match on any token). If ambiguous, pick the one defined earliest.

Node label: `<file>\n(<primary_symbol>)` (Mermaid uses `<br/>`, PlantUML uses `\n`).
Node ID: `<file>` with `/` → `_`, `.` → `_`, stripped of final `py` extension marker.

### Step 2: Enumerate edges

For each file, parse imports via language-specific regex:

- Python: `^(from (?P<module>[\w.]+) import|import (?P<module>[\w.]+))`.
- Rust: `^use (?P<module>[\w:]+)`.
- JS/TS: `^import .* from ["'](?P<module>[^"']+)["']`.
- Go: `^\s*"(?P<module>[\w/.]+)"` within an `import (...)` block.

For each imported module, resolve to a file path:
- Try `<src_root>/<module_path>.py` (replacing `.` with `/`).
- Try `<src_root>/<module_path>/__init__.py`.
- Try other language-appropriate conventions.

If the resolved path is in `files`, emit an edge `<importer_file> → <resolved_file>`.

If the resolved path is outside `files` but inside `src_root` AND `include_external=true`, add a ghost node `external::<module>` and emit the edge.

If the import resolves outside `src_root` entirely (stdlib, third-party), drop silently.

### Step 3: Emit diagram

Resolve renderer per shared doc's resolution order (`renderer_override` → `pharaoh.toml [pharaoh.diagrams].renderer` → default `mermaid`).

Emit the diagram with direction `TD` (top-down, showing call depth). Caption: `<feat_id> — component composition`.

For ghost nodes (when `include_external=true`), group them visually apart where the renderer supports it:
- Mermaid: separate `subgraph External` block.
- PlantUML: `package "external" { ... }` block.

Ghost-node styling: dashed outline + muted color (specifics per renderer — consult `shared/diagram-tailoring.md` for the type_styles lookup).

### Step 4: Return

Single RST block. No prose before or after.

## Failure modes

- `files` empty → FAIL.
- Any file in `files` unreadable → log + skip that file (do not abort unless all files unreadable).
- Cycles in the import graph → emit the diagram anyway (Mermaid/PlantUML handle cycles); log a note.
- Zero edges resolved inside `files` → emit nodes only, log a note ("no intra-scope edges detected — check files list or use include_external=true").
- `include_external=true` AND zero in-scope edges AND zero external edges → still emit nodes only, log note.

## Non-goals

- No runtime / call-graph inference — that is `pharaoh-feat-flow-extract`.
- No type hierarchy — that is `pharaoh-class-diagram-draft` (hand-authored) or a future `pharaoh-feat-class-extract`.
- No transitive import resolution beyond one hop — depth > 1 explodes scope.
- No dead-code detection — every file in `files` is a node, whether imported or not.

## Last step

After emitting the artefact, invoke `pharaoh-diagram-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must regenerate (via `pharaoh-diagram-regenerate` if available, or by re-invoking this skill with the findings as input).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

---
name: pharaoh-feat-flow-extract
description: Use when reverse-engineering a feat and you need to derive a sequence diagram showing the control flow from its entry point through its source files. Walks the call graph up to a bounded depth and emits a Mermaid or PlantUML sequence diagram whose output shape matches pharaoh-sequence-diagram-draft. Complements pharaoh-feat-component-extract (static view); this is the dynamic view.
---

# pharaoh-feat-flow-extract

## When to use

Invoke after `pharaoh-feat-file-map` has produced a `{feat_id, files, entry_point}` mapping (with `entry_point` naming the file+symbol where flow begins — typically a CLI command, HTTP route, test entry, or event handler), when you want to see the call chain that realizes the feat. Output is a sequence diagram matching `pharaoh-sequence-diagram-draft`'s shape so downstream tooling treats it identically.

Do NOT use for static architecture — that is `pharaoh-feat-component-extract`. Do NOT use when `entry_point` is not known — the skill fails fast rather than inventing one.

## Tailoring awareness

Shared tailoring rules: see `shared/diagram-tailoring.md`. Reads `[pharaoh.diagrams]` and `[pharaoh.diagrams.sequence]` from `pharaoh.toml` for renderer choice. Respects `on_missing_config` per shared `check → propose → confirm`.

Safe-label rules: see `shared/diagram-safe-labels.md`. **Critical for this skill:** messages derived from call expressions (`foo(a; b, c)`) often contain `;` which Mermaid 11 treats as a statement terminator, and path fragments like `csv/export.py` are not valid participant IDs. Rules to apply before emit: (a) replace `;` in any message label with `,`; (b) use participant aliases (`participant Export as csv/export.py`), never raw paths as IDs; (c) strip backticks from symbol names. A message label containing `;` (e.g. `J->>J: filter by type; skip SET/Folder`) parses cleanly under `sphinx-build -nW` but renders as `Syntax error in text` in the browser — sanitisation catches this class before emit.

## Atomicity

- (a) Indivisible — one feat + one file list + one entry_point in → one sequence diagram out. No multi-scenario bundling. No mutation. No req emission.
- (b) Input: `{feat_id: str, feat_title: str, files: list[str], entry_point: {file: str, symbol: str}, project_root: str, src_root: str, renderer_override?: "mermaid"|"plantuml", max_depth?: int, on_missing_config?: "fail"|"prompt"|"use_default", papyrus_workspace?: str, reporter_id: str}`. Output: one RST directive block matching `pharaoh-sequence-diagram-draft`'s output shape. Default `max_depth=5`.
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-feat-flow-extract/`:
  - `input_feat.yaml` declares `entry_point: {file: commands/csv.py, symbol: export}`.
  - `input_files/` is shared with `pharaoh-feat-component-extract` — the call chain `commands.csv:export → csv.export:run_export → csv.writer:CSVWriter.write_header / write_rows`.
  - `expected_diagram.rst` has 3 participants (one per file touched) and the 4 messages representing the call chain.

  Scorer:
  1. Output starts with the renderer's sequence-diagram directive.
  2. Every participant in the call chain appears (one per distinct file).
  3. Messages render in call order with correct arrow syntax.
  4. Message count equals call count at `max_depth=5` (should resolve to 4 for this fixture).
  5. Participants are declared in first-seen order (entry point first).
  6. Output shape matches `pharaoh-sequence-diagram-draft`.

  Pass = all 6.
- (d) Reusable for any language whose call-graph the extractor supports. Python initial target (AST or regex).
- (e) Composable: one feat per call. A plan emitted by `pharaoh-write-plan` may include a `foreach` task over feats (with entry_point set) that dispatches this skill alongside `pharaoh-feat-component-extract` in the same `parallel_group`. Never invokes other skills.

## Input

- `feat_id`: diagram caption prefix.
- `feat_title`: human-readable, shown in caption.
- `files`: list of source file paths relative to `src_root`. Only calls resolving to files in this list are traced; calls to stdlib / third-party / out-of-scope files are silently dropped (they are not part of the feature).
- `entry_point`:
  - `file`: path relative to `src_root` — must be in `files`.
  - `symbol`: name of the function or method where flow begins.
- `project_root`, `src_root`: as in Task 19's skill.
- `renderer_override` (optional): per shared doc.
- `max_depth` (optional): maximum recursion depth when walking the call chain. Default `5`.
- `on_missing_config`, `papyrus_workspace`, `reporter_id`: standard.
- `scenarios` (optional): list of scenario names, default `["default"]`. Each scenario produces one diagram block. Scenario names drive annotations in the output (e.g. `:caption: FEAT_x — flow, scenario: error_handling`). Project tailoring declares the canonical scenario set via `.pharaoh/project/diagram-conventions.yaml > dynamic_view_scenarios`. See [`shared/diagram-view-selection.md`](../shared/diagram-view-selection.md).

## Output

Output is a JSON document with shape:

```json
{
  "diagrams": [
    {
      "scenario": "default",
      "diagram_block": ".. mermaid::\n   :caption: FEAT_x — flow\n\n   sequenceDiagram\n   ...",
      "element_count": 7,
      "renderer": "mermaid"
    }
  ]
}
```

One entry per scenario. Callers invoke `pharaoh-diagram-review` per entry (plan template foreach-expands over `diagrams[]`).

## Process

### Step 1: Locate entry point

Read `<src_root>/<entry_point.file>`. Locate the definition of `<entry_point.symbol>` via regex:

- Python: `^(\s*)(def|async def|class) <symbol>\b`.
- Other languages per shared doc.

If not found → FAIL: `"entry_point.symbol <symbol> not found in <entry_point.file>"`.

Capture the body of the symbol (lines until the next line with indentation ≤ the symbol's definition line).

### Step 2: Walk call chain up to max_depth

Starting from the entry symbol's body, identify direct function/method calls. Regex (Python):

- Bare calls: `(?<!\.)(?P<name>\w+)\(` (a bare identifier followed by `(`, not preceded by `.`).
- Method calls: `\.(?P<name>\w+)\(`.
- Constructor calls: `(?P<name>[A-Z]\w+)\(` (uppercased → probably a class instantiation).

For each call, resolve the target:

- Check if the name matches a top-level symbol defined in any of the `files` (use the primary-symbol detection from Task 19's skill). If so, record `(from_file, to_file, call_label)` where `call_label` is `<symbol>()` or `<method_name>()`.
- If the call resolves to a stdlib / third-party / imported-external symbol, drop it silently.
- If the call resolves to a local helper within the same file, drop it (same-file calls clutter the diagram; the participant-per-file abstraction collapses them).

Recurse into resolved cross-file calls up to `max_depth` (default 5). Collect all resolved cross-file calls in call order (the order they appear in the body, top-to-bottom).

### Step 3: Emit sequence diagram

Resolve renderer per shared doc. Declare one participant per distinct file encountered in the call chain, in first-seen order. Emit messages in the order collected.

Arrow syntax:

- Synchronous call: Mermaid `->>`, PlantUML `->`.
- If the call target is `async def`, use async arrow: Mermaid `-)`, PlantUML `->>`.

No return arrows are emitted by default — they clutter at this granularity. Callers who want them can use `pharaoh-sequence-diagram-draft` with explicit messages.

Caption: `<feat_id> — flow from entry point`.

### Step 4: Return

Single RST block. No prose.

## Failure modes

- `entry_point.file` not in `files` → FAIL: `"entry_point.file <file> is not in the files list"`.
- `entry_point.symbol` not found in `entry_point.file` → FAIL per Step 1.
- Zero calls detected from the entry symbol's body → emit a minimal diagram with one participant (the entry point's file) and a self-note `Note over <participant>: entry point has no cross-file calls` instead of failing.
- Max depth exceeded → truncate at depth, log a note.

## Non-goals

- No return-arrow inference. Use `pharaoh-sequence-diagram-draft` if needed.
- No activation-bar insertion (PlantUML activates/deactivates).
- No concurrent / async branch handling beyond marking the arrow shape. Complex async flow is hand-authored via `pharaoh-sequence-diagram-draft`.
- No multi-entry-point diagrams. One entry → one diagram. If a feat has multiple entry points (e.g. a CLI with two subcommands), the orchestrator dispatches the skill twice.
- No code-to-sequence inference below function granularity (no per-statement trace). The unit of traceability is a function/method call crossing file boundaries.

## Last step

After emitting the artefact, invoke `pharaoh-diagram-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must regenerate (via `pharaoh-diagram-regenerate` if available, or by re-invoking this skill with the findings as input).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

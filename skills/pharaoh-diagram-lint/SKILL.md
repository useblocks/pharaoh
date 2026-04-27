---
name: pharaoh-diagram-lint
description: Use when running a terminal validation step over a directory of RST files to catch Mermaid / PlantUML parse failures that sphinx-build cannot detect. Extracts every `.. mermaid::` and `.. uml::` block and pipes it to the real renderer parser (mmdc / plantuml -checkonly). Returns structured findings. Does NOT modify the RST files.
---

# pharaoh-diagram-lint

## When to use

Invoke after a reverse-engineering or diagram-emission plan has written RST files containing Mermaid or PlantUML diagram blocks, as a terminal check before the plan's `pharaoh-quality-gate` consumes the results. `sphinx-build` does not validate diagram bodies at build time — it hands them to the browser renderer unchanged. A parse failure is therefore invisible in CI logs and surfaces only when a human opens the page. This skill is the parser in the validation loop.

Do NOT invoke to modify diagrams (this skill is read-only). Do NOT invoke on a single RST file where you already hand-validate with `mmdc` — that workflow does not need an atomic skill. Do NOT use this skill to replace `pharaoh-quality-gate`; it is one of the checks the gate consumes.

## Why this skill exists

Mermaid diagrams can pass `sphinx-build -nW --keep-going -b html` with zero warnings while rendering as `Syntax error in text` in the browser. Prose review of surrounding artefacts does not catch this because it has no Mermaid parser. Running every diagram through `@mermaid-js/mermaid-cli` (matching the version sphinxcontrib-mermaid pins) surfaces parse errors the sphinx build misses.

Structural validation of RST (directive options, needs schema) is necessary but insufficient. Every artefact type with its own render pipeline needs its own parser in the validation loop. This skill is that parser for Mermaid and PlantUML.

## Atomicity

- (a) **Indivisible.** One directory in → one findings report out. No RST mutation. No diagram authoring. No scope outside Mermaid/PlantUML block parsing.
- (b) **Typed I/O.**
  - Input: `{docs_dir: str, strictness: "fail_on_any" | "report_only", renderers?: list["mermaid" | "plantuml"], mermaid_cli?: str, plantuml_cli?: str, reporter_id: str, papyrus_workspace?: str}`.
  - Output: `{findings: list[{file: str, line: int, renderer: "mermaid"|"plantuml", block_index: int, parser_exit_code: int, parser_stderr: str, severity: "error"|"warning"}], summary: {blocks_scanned: int, blocks_failed: int, renderers_covered: list[str]}, status: "pass" | "fail" | "degraded"}`. `degraded` = scanner ran but at least one renderer CLI was not installed; findings cover the renderers that WERE available.
- (c) **Execution-based reward.** Fixture `pharaoh-validation/fixtures/pharaoh-diagram-lint/`:
  - `docs/good.rst` — two valid Mermaid blocks (one sequenceDiagram, one flowchart).
  - `docs/bad_semicolon.rst` — one Mermaid sequence diagram with a `;` in a message label (prior dogfooding defect).
  - `docs/bad_pipe.rst` — one Mermaid flowchart with an unescaped `|` in an edge label.
  - `docs/bad_plantuml.rst` — one `.. uml::` block with an unterminated `@startuml`.
  - `docs/good.rst` must score zero findings; each `bad_*.rst` must produce at least one finding with `parser_exit_code != 0`.
  - Scorer runs `pharaoh-diagram-lint` against `fixtures/pharaoh-diagram-lint/docs` with `strictness: report_only` and asserts: `summary.blocks_scanned == 5`, `summary.blocks_failed == 3`, one finding per bad file, `status == "fail"`.
  - Idempotence: re-running on the same directory returns the same findings list (order stable by `file, line`).
- (d) **Reusable.** Any directory of RST. Not tied to Pharaoh pipelines — CI integrations, editor-in-the-loop lint, pre-commit hooks can use it.
- (e) **Composable.** `pharaoh-quality-gate` reads the `findings` and aggregates into its report under a `diagram_lint` section. The reverse-engineer-project template adds this skill as a dependency of `quality_gate`.

## Input

- `docs_dir` (required): absolute path to a directory. Scanner walks `**/*.rst` under it.
- `strictness` (required): `"fail_on_any"` returns `status: "fail"` if any finding has `severity: error`; `"report_only"` always returns the findings list with `status: "fail"` or `"pass"` based on findings but does not treat this as a skill failure. Plans wire this to `pharaoh.toml [pharaoh.quality_gate].strict`.
- `renderers` (optional): subset of `["mermaid", "plantuml"]`. Default: both. Useful for projects that emit one renderer only.
- `mermaid_cli` (optional): command name / path to the Mermaid CLI. Default `"mmdc"` (on `$PATH`). The skill uses whatever is resolved; no bundled tool. If unresolved and mermaid blocks are present, emit a `degraded` status + warning naming the installation command (`npm install -g @mermaid-js/mermaid-cli@11`).
- `plantuml_cli` (optional): command name / path to the PlantUML CLI. Default `"plantuml"`. Fallback installation command: `brew install plantuml` or `apt-get install plantuml`.
- `reporter_id` (required): short agent id, passed to `pharaoh-finding-record` calls.
- `papyrus_workspace` (optional): path to `.papyrus/` for recording findings as dedup-aware records. If absent, findings are only returned; not persisted.

## Output

Single JSON object. Example:

```json
{
  "findings": [
    {
      "file": "docs/source/spec/feature/jama.rst",
      "line": 66,
      "renderer": "mermaid",
      "block_index": 2,
      "parser_exit_code": 1,
      "parser_stderr": "Error: Parse error on line 3: ... Expecting 'SOLID_ARROW'... got 'NEWLINE'",
      "severity": "error"
    }
  ],
  "summary": {
    "blocks_scanned": 5,
    "blocks_failed": 1,
    "renderers_covered": ["mermaid", "plantuml"]
  },
  "status": "fail"
}
```

`line` refers to the starting line of the `.. mermaid::` / `.. uml::` directive inside the RST file (where a human would look to fix it). `block_index` is the zero-indexed position of the block within the file (0 = first diagram in the file, 1 = second, etc.) to disambiguate when multiple blocks live in the same file.

## Process

### Step 1: Enumerate RST files under `docs_dir`

Use the Glob tool to list `${docs_dir}/**/*.rst`. If empty, emit warning `"no RST files under docs_dir"` and return `{findings: [], summary: {blocks_scanned: 0, blocks_failed: 0, renderers_covered: []}, status: "pass"}`.

### Step 2: Extract diagram blocks

For each file, scan for directive openings. Recognise:

- `.. mermaid::` — start of a Mermaid block. Body = subsequent lines indented by ≥ 3 spaces.
- `.. uml::` — start of a PlantUML block.
- `.. plantuml::` — alias for `.. uml::` (some projects use this spelling).

A block ends at the first subsequent line that is either (a) non-blank and indented by < 3 spaces, or (b) end of file. Directive options (e.g. `:caption:`) between the opening line and the body are skipped (not part of the renderer input).

Record for each block: `{file, start_line, renderer, block_index, body}` where `body` is the concatenation of body lines with the leading indent stripped.

### Step 3: Check CLI availability

For each renderer whose blocks were found (AND requested by `renderers` input):

- Run `<cli> --version` via Bash. Capture exit code.
- If non-zero, emit a degraded-status warning naming the renderer + install command. Skip parsing for this renderer (findings empty for it).

### Step 4: Parse each block

For each block whose renderer CLI is available:

1. Write `body` to a temp file (`/tmp/pharaoh-diagram-lint-${pid}-${idx}.mmd` or `.puml`).
2. Invoke the parser:
   - **Mermaid**: `<mermaid_cli> -i <tmp_in> -o <tmp_out.svg>`. mmdc 11.x requires an output path with a recognised extension (`.svg` / `.png` / `.pdf` / `.md` / `.markdown`); a sentinel like `/dev/null` is rejected with `Output file must end with ...`. Delete `<tmp_out.svg>` afterwards.
   - **PlantUML**: `<plantuml_cli> -checkonly <tmp>`. `-checkonly` parses without rendering.
3. Determine parse failure:
   - **Mermaid** — mmdc 11.x returns exit code 0 even when the mermaid parse fails inside puppeteer. Treat stderr as authoritative: if stderr contains any of `"Error:"`, `"Parse error"`, `"Expecting "`, or `"UnknownDiagramError"`, the block failed. Callers synthesise a non-zero `parser_exit_code` in the finding for consistency across renderers.
   - **PlantUML** — `plantuml -checkonly` exits 200 on parse failure. Exit code alone is reliable.
4. On failure, emit a finding with the captured stderr (trimmed to the first 200 chars, after stripping mmdc's success noise like `Generating single mermaid chart`).

Each finding is:

```json
{
  "file": "<relative path from docs_dir>",
  "line": <start_line of the directive>,
  "renderer": "<mermaid|plantuml>",
  "block_index": <int>,
  "parser_exit_code": <int>,
  "parser_stderr": "<first 20 lines, stripped of CLI framing>",
  "severity": "error"
}
```

### Step 5: Aggregate and return

Sort findings by `(file, line, block_index)` for stable output.

Compute `summary`:
- `blocks_scanned`: total blocks extracted (across all renderers).
- `blocks_failed`: length of findings list.
- `renderers_covered`: renderers whose CLI was available and actually parsed at least one block.

Compute `status`:
- `degraded` if any requested renderer was unavailable AND blocks of that renderer exist.
- `fail` if any finding has `severity: error` AND `strictness == "fail_on_any"`, OR if `strictness == "report_only"` AND findings list is non-empty.
- `pass` otherwise.

### Step 6: Optional Papyrus persistence

If `papyrus_workspace` is provided, for each finding invoke `pharaoh-finding-record` with:

- `category`: `"diagram_parse_failure"`
- `subject_id`: `<file>:L<line>:B<block_index>` (deterministic id: re-running on the same broken diagram returns `"duplicate"`, so findings don't accumulate across runs)
- `body`: the stderr excerpt
- `reporter_id`: the input `reporter_id`
- `tags`: `["renderer:<name>", "origin:diagram-lint"]`

Skip this step if `papyrus_workspace` is absent — in-memory return is sufficient for plans that do not use shared memory.

## Failure modes

| Condition                                         | Response                                                     |
| ------------------------------------------------- | ------------------------------------------------------------ |
| `docs_dir` missing                                | FAIL: `"docs_dir <path> does not exist"`.                    |
| No RST files under `docs_dir`                     | Return empty findings with warning; `status: pass`.          |
| Mermaid CLI unresolved, mermaid blocks present    | `status: degraded`; warning with install command; findings empty for mermaid. |
| PlantUML CLI unresolved, plantuml blocks present  | `status: degraded`; warning with install command; findings empty for plantuml. |
| CLI reports parse failure (exit code OR stderr markers) | Emit finding. Continue with next block. mmdc uses stderr markers; plantuml uses exit code 200. |
| CLI hangs (> 30s)                                 | Kill child process; emit finding with `parser_stderr: "timeout after 30s"`. |
| Temp-file write fails                             | Abort with FAIL naming the temp path.                        |

## Non-goals

- **No auto-fix.** The skill reports; it does not patch RST files. Fixing belongs to whatever emitted the broken diagram (usually a `pharaoh-*-diagram-draft` or `pharaoh-feat-*-extract` skill), or to a human.
- **No render output.** `mmdc` can render PNG/SVG; we discard that. Rendering is sphinx-build's job at HTML build time.
- **No semantic linting.** This skill checks syntactic validity per the renderer parser. Style complaints ("this diagram has too many participants") belong in a future `pharaoh-diagram-review` skill.
- **No other renderers.** Graphviz (`.. graphviz::`), KaTeX (`:math:`), and others are out of scope. Extend the skill (new renderer entries in Step 2's recognition table) when their silent-failure mode becomes a concrete problem.

## Advisory chain

After emitting findings:

- If `status == "fail"` and strictness is `"fail_on_any"`: downstream `pharaoh-quality-gate` should flip to red. Callers should not ship the documentation build.
- If `status == "degraded"`: the missing CLI is a local-environment gap. Install it and re-run before considering the lint report authoritative.
- If `status == "pass"`: does NOT guarantee every diagram is *good*. Semantic correctness (right messages in the right order, right participant set) is unverified — this skill catches syntactic defects only.

## Composition

- The `reverse-engineer-project.yaml.j2` template adds `pharaoh-diagram-lint` as a dependency of `pharaoh-quality-gate` (and the gate's input includes the findings).
- `pharaoh-quality-gate` SHOULD expose a `diagram_lint` section in its aggregated report summarising the findings count per renderer and the first 5 errors verbatim.
- A future `pharaoh-render-check` generalisation covering Graphviz, KaTeX, etc. can subsume this skill; until then this is the only parser-in-the-loop validator for Mermaid and PlantUML.

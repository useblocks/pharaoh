---
name: pharaoh-req-from-code
description: Use when reading one source file and emitting one or more requirement RST directives (typed by `target_level`) describing the observable behavior in that file. Queries shared Papyrus for canonical terms before naming concepts; writes newly surfaced concepts back. Does not draft architecture, plans, or FMEA.
---

# pharaoh-req-from-code

## Shall-clause rules

The seven rules below govern what a CREQ's body looks like. All seven apply to every emission; violations of any rule mean the emission is a draft, not a valid CREQ.

### Rule 1 — Subject is the component (or an external actor)

The grammatical subject of the shall clause is either:

1. the component / capability (e.g. "The CSV Importer", "The export CLI", "The API client"). The component name comes from the parent feat title, from a named role inside the feat scope, or from the project's `artefact-catalog.yaml`.
2. an external actor (user, operator, caller, third-party service) whose action the component shall respond to — acceptable when the feat is an interactive CLI, an API, or any user-facing interface. Example: "The authenticated user shall receive a non-zero exit code on malformed input."

Never a Python function, class, private method, or file.

Code-narration subjects (❌) vs component subjects (✅):

| Bad | Good |
|---|---|
| ``from_source_a`` shall call ``check_license`` | The Source A Connector shall reject unlicensed use |
| ``_apply_cli_overrides`` shall override credentials | The Source A CLI shall accept server credentials on the command line |
| ``FooClient._classify_connection_error`` shall raise ``FooAuthenticationError`` on HTTP 401 | The Source A Connector shall signal an authentication failure when the server rejects the configured credentials |
| ``ItemLoader`` shall load items from ``ImporterConfig.input_path`` via ``load_items`` | The Importer shall read items from the configured input path |

Tests: the component form is falsifiable by a tester who can't read the source (black-box), stable across refactors (renaming `_apply_cli_overrides` does not invalidate the CREQ), and traceable to the feat via `:satisfies:`.

### Rule 2 — No internal implementation details in the body

No internal / private function names, no leading-`_` methods, no class-dot-method references, no file paths, no line numbers ever (`around line 165`, `in commands/foo.py`, `at the top of the module` — all banned). Traceability to code lives in `:source_doc:`; the shall clause carries behavior. These two jobs stay separate.

Known prior failures this rule catches:

- `"record_key drives the create-vs-update decision"` — names an internal field AND gets the mechanism wrong (actual decision variable is a different id attribute on the same record).
- `"parse_timestamp raises on unparseable input"` — names an internal function AND misstates the behavior (the function returns `None`; the caller raises).

A clean behavioral shall with zero backticks and one `:source_doc:` is preferred over a code-narration shall with ten backticks.

### Rule 3 — `:source_doc:` must point at the implementing source code file

Every emitted CREQ carries `:source_doc:` pointing at a real source file — typically `.py`, `.rs`, `.ts`, `.go`, `.c`, `.cpp`, `.java` under the project's source tree (e.g. `src/<project>/csv/csv2needs.py`). Pointing `:source_doc:` at the spec RST file itself or at a prose feature doc is a validation failure — the spec RST is where the requirement lives, not where the behavior is implemented.

When a CREQ's behavior spans multiple source files, pick the file that owns the primary observable (usually the converter module, not a CLI dispatcher). `pharaoh-req-code-grounding-check` axis #8 (`source_doc_resolves`) fails if the cited file is the spec RST or missing entirely.

### Rule 4 — CREQ adds constraint beyond the parent feat

A CREQ whose shall clause paraphrases the feat capability with the same subject, verb, and scope is tautological and MUST NOT be emitted.

Test before every emission: *what constraint does this CREQ impose that the feat body alone does not?* Answers that count: a concrete pre-condition, a post-condition, an error contract, a default value, an ordering guarantee, a quantitative bound, a specific field / flag / command name. Answers that don't: just naming a sub-capability in the imperative.

Bad (tautology) — feat says "The CSV Connector enables bidirectional exchange between Sphinx-Needs and CSV files"; CREQ says "The CSV Importer shall convert a user-supplied CSV file into a needs.json file when the user invokes `<cli> <subcmd> from-csv`" — zero added constraint.

Good — "The CSV Importer shall fail with a non-zero exit code and a single-line error message on the first row whose mapped `id` column is missing or empty, without writing a partial `needs.json`" — specific precondition, specific post-condition, specific boundary observable.

### Rule 5 — Enumerate boundary-observable code structures exhaustively

For each `:source_doc:` file, enumerate and emit one CREQ per boundary-observable structure:

1. **Every raised exception class that escapes the module's public surface.** "The component emits `FooError` when <condition>."
2. **Every published config key the module reads.** TOML keys, env vars, dataclass fields — one CREQ per key, naming the key and the default.
3. **Every public function or CLI subcommand exposed by the module.** CLI subcommand = one CREQ; exported library function = one CREQ.

Expected floor per typical connector module (200-500 LOC, 3-8 exception classes, 5-10 config keys, 1-3 public functions): **12-20 CREQs per module**. Under-decomposition below this floor means structures got bundled into compound shalls — split them.

Each emitted block's body has exactly one `shall` clause. Zero intra-clause conjunctions joining modal-verb phrases (`, and shall` / ` and shall` / ` or raise` / `, or ` — all splits). Multiple observable behaviors = multiple CREQs. Intra-clause conjunctions are a hard fail regardless of behavioral quality; split the block before returning.

### Rule 6 — `:verification:` field is required

Every emitted CREQ carries `:verification:` with at minimum the placeholder `tc__TBD`. Absence is a schema failure. If the project uses a different link name for the req→test relation (`verifies`, `covered_by`), declare it in `[[needs.extra_links]]`; the default placeholder stays required.

### Rule 7 — Backticks are for code / protocol tokens only

Backticks signal "copy this string verbatim — it is a code symbol, config key, or protocol token". NOT for format acronyms (``CSV``, ``JSON``, ``XML``, ``TOML``, ``HTML``), document-type nouns (``document``, ``file``, ``row``), or emphasis (``default``, ``required``).

Test: would a tester copy-paste this string into test code or configuration? If yes, backtick it. If not, leave it bare.

Backticks ARE acceptable on external-surface identifiers: CLI flags (``--host``), env vars (``APP_LICENSE_KEY``), TOML config keys (``[myapp.export_config]``, ``links_delimiter``), HTTP routes (``/itemtypes``), protocol tokens (``HMAC-SHA256``).

### Config-value citation (see Rule 3 + Rule 7)

Example: a consumer module that reads `self.config.output_format` cites ``output_format`` (its own reference form), not the default-value literal (``default_format``) which lives in the config module. Citing the default-value form creates a false paper-trail — the grounding-check axis will fail because the shall clause names a symbol the cited file does not contain.

## When to use

Invoke with a single source file (any language) assigned to this agent and (optionally) a shared Papyrus workspace for cross-agent terminology coordination. Emit one requirement (of type `target_level`) per distinct boundary-observable behavior expressed in the file. Do NOT emit reqs for behavior not grounded in the file (that is drafting, not reverse-engineering). Do NOT attempt architecture, verification plans, or FMEA — those are separate skills.

## Tailoring awareness

Two axes are tailored, both read at runtime from the consumer project's `ubproject.toml` / `pharaoh.toml`:

**Type axis** — need types and ID conventions are project-specific. Read `[[needs.types]]` entries from `ubproject.toml` (or `.pharaoh/project/id-conventions.yaml` if present) — each has `directive` and `prefix`. Do NOT hardcode `comp_req` as the only acceptable type. The caller passes `target_level` — use it verbatim as the directive name (in `rst` emit) or as the `type` field (in `codelinks_comment` emit).

**Emit axis** — whether to emit RST directive blocks or sphinx-codelinks-compatible one-line comments. Resolution order:

1. `emit_override` input (per-call).
2. `pharaoh.toml [pharaoh.codelink_comments].mode` — `"codelinks"` → `codelinks_comment`; `"backref"` or absent → `rst`.
3. Auto-detect: `ubproject.toml` contains `[codelinks.projects.*]` → `"codelinks_comment"`; otherwise `"rst"`.
4. Fallback: `"rst"`.

If `on_missing_config == "prompt"` (default) AND tailoring is missing (no `target_level` in `[[needs.types]]`, or emit mode unresolvable), the skill returns `{status: "needs_confirmation", proposal: {...}}` with a tailoring patch the caller can confirm. Caller confirms → tailoring gets written (typically via `pharaoh-tailor-fill`) → re-invoke with `on_missing_config="use_default"` for silent proceed.

## Atomicity

- (a) Indivisible — one file in → N reqs out. No I/O beyond file read + optional Papyrus query/write + req emit. Emits in exactly one representation per call (`rst` OR `codelinks_comment`).
- (b) Input: `{file_path, target_level, shared_context_path?, papyrus_workspace?, reporter_id, parent_feat_ids?, emit_override?, codelinks_project_name?, on_missing_config?, allowed_ids?, split_strategy?}`. Output: list of RST directive blocks OR list of sphinx-codelinks one-line comments, prefixed with `# emit=rst` or `# emit=codelinks_comment`. On missing tailoring with `on_missing_config=prompt`: single JSON object `{status: "needs_confirmation", proposal}`.
- (c) Reward: language-parametric fixture — given `test_fixture.<ext>` (`.py` / `.cpp` / `.rs` / `.ts`) containing exactly 3 named symbols (`FooBar`, `BazQux`, `Quux`), emitted reqs must mention all 3 by canonical name. Directive name must equal `target_level`. If `parent_feat_ids` is non-empty, every emitted block MUST contain `:satisfies: <id1>, <id2>, ...` with all parents comma-joined.
- (d) Reusable across reverse-engineering workflows, spec drafting, standalone CI "are there reqs for this code?" gates.
- (e) Composable — strictly one phase. Never invokes `pharaoh-arch-draft`, `pharaoh-fmea`, `pharaoh-plan`.

## Input

- `file_path`: absolute path to the source file (any language).
- `target_level`: requirement artefact directive name as declared in the consumer project's `ubproject.toml` (e.g. `"comp_req"`, `"impl"`, `"spec"`). ID prefix is `target_level` + `__` unless `[[needs.types]].prefix` overrides.
- `shared_context_path` (optional): companion source file read by all agents in the fan-out (e.g. `common.cpp`). Read but NOT reverse-engineered.
- `papyrus_workspace` (optional): path to `.papyrus/` for canonical-term coordination. Absent → no-memory mode (skip Steps 1 and 3).
- `reporter_id`: short identifier for this agent (e.g. `req-from-code:csv2needs.py`).
- `parent_feat_ids` (optional): list of parent feature IDs. When non-empty, every emitted block gets `:satisfies: <id1>, <id2>, ...` comma-joined.
- `allowed_ids` (optional): pre-allocated ID list. When provided, emitter MUST NOT invent IDs outside this list; emits only `len(allowed_ids)` reqs max; overflow logged as a warning comment.
- `split_strategy` (optional): `"single"` (default, whole file as one scope, target 1-5 reqs), `"top_level_symbols"` (per top-level symbol, target 1-3 reqs/symbol), or `"sections"` (per `# ---` / `// ===` horizontal-rule marker, target 1-3 reqs/section). Plans supply this via `${heuristics.split_strategy(...)}`.

## Output

Single one-line header names the emit mode (`# emit=rst` or `# emit=codelinks_comment`).

### `emit=rst`

Zero or more RST directive blocks separated by one blank line. Directive name equals `target_level`. Each block:

```
.. <target_level>:: <short_title>
   :id: <id_prefix><snake_case_id>
   :status: draft
   :satisfies: <parent_1>, <parent_2>, ...    # only if parent_feat_ids is non-empty
   :source_doc: <path to implementing source file>
   :verification: tc__TBD

   The <Component subject> shall <observable behavior>.
```

`<id_prefix>` defaults to `target_level` (`comp_req` → `comp_req__foo_01`). If `[[needs.types]].prefix` declares `"CREQ_"`, use `CREQ_foo_01`.

### `emit=codelinks_comment`

Zero or more one-line strings matching the project's `[codelinks.projects.<name>.analyse.oneline_comment_style]`:

```
@ <title>, <id>, <target_level>, [<parent_1>, <parent_2>, ...]
```

- Tailored `start_sequence` (default `@`).
- Tailored `field_split_char` (default `,`) with surrounding spaces.
- Field order matches tailored `needs_fields`.
- Values escaped per sphinx-codelinks rules.
- No language comment prefix (that is `pharaoh-req-codelink-annotate`'s job).

### `status == "needs_confirmation"`

When tailoring is missing and `on_missing_config == "prompt"`, output is a single JSON object. Downstream consumers check for this shape before parsing.

## Output schema

The orchestrator (or `pharaoh-output-validate`) validates each emitted block in two stages.

**Stage 1 — block recognizer (Python regex, `re.MULTILINE`):**

```regex
^\.\. (?P<directive>[a-z_]+)::\s+(?P<title>.+)$
(?P<options>(?:^   :[a-z_]+:.*$\n?)+)
(?:^\n   (?P<body>[\s\S]+?))?
(?=^\.\.\s|\Z)
```

Identifies one directive block bounded by the next `.. ` at column 0 or end of input. `re.MULTILINE` without `re.DOTALL` keeps `.` line-bounded; options cannot leak into adjacent blocks.

**Stage 2 — option enumeration (on the recognizer's `options` capture):**

```regex
^   :(?P<option>[a-z_]+):\s*(?P<value>.*)$
```

`re.finditer` with `re.MULTILINE` enumerates every option/value pair.

**Validator checks (per block):**

1. Stage 1 matched — block is well-formed.
2. `directive` capture equals input `target_level`.
3. Stage 2 yields at least `id`, `status`, `source_doc`, and `verification`.
4. If `parent_feat_ids` was provided: `satisfies` (or tailored child→parent link name) is among options with every parent id in its value.
5. Every option name is either declared in `ubproject.toml` `[[needs.types]]`, a built-in sphinx-needs option, or a Pharaoh convention option. Reject unknown names (catches typos like `subsatisfies`).
6. After the last matched block, remaining input is only `\n*`.
7. If `allowed_ids` was provided: every emitted `id` is a member of `allowed_ids`.

**`emit=codelinks_comment`** — each line must parse via sphinx-codelinks `oneline_parser.parse_line()` against the tailored `oneline_comment_style`.

## Process

### Step 1: Query Papyrus for canonical terms BEFORE naming

Only applies if `papyrus_workspace` is provided. For each type / function / concept you may name in a req:

1. Form a short semantic query ("what do we call the subsystem that supervises other monitors").
2. Invoke `pharaoh-context-gather` with `mode="semantic"`. Semantic mode is required — substring recall silently misses morphological synonyms.
3. If a canonical appears in the top-3 results, use its exact spelling (preserve case).
4. If no match, plan to introduce a new canonical in Step 3.

### Step 2: Read the source file

Read `file_path` and, if provided, `shared_context_path`. Identify boundary-observable behaviors grounded in control flow and data flow. Ignore internal helpers, log messages, assertion text.

Apply `split_strategy`:

- `"single"` (default): whole file as one scope. Target 1-5 reqs.
- `"top_level_symbols"`: enumerate top-level symbols via the patterns in [`../shared/public-symbol-patterns.md`](../shared/public-symbol-patterns.md). Emit per symbol. Target 1-3 reqs per symbol.
- `"sections"`: split at `^#\s*={3,}` / `^//\s*={3,}` markers. Target 1-3 reqs per section.

In plan-driven runs the `${heuristics.split_strategy(...)}` helper picks per-file by LOC (≤500 → single; 500-2000 with markers → sections; else → top_level_symbols).

### Step 3: Record newly surfaced concepts in Papyrus

Only applies if `papyrus_workspace` is provided. For each concept you will mention and that Step 1 did not return, invoke `pharaoh-decision-record`:

- `type`: `"fact"`
- `canonical_name`: idiomatic casing for the source language (CamelCase for types; snake_case for functions/fields in Python/Rust/C; camelCase in TypeScript/Java). Preserve what the source uses.
- `body`: one sentence.
- `reporter_id`: your `reporter_id` input.
- `tags`: `["origin:req-from-code", "file:<basename>"]`.

On `"duplicate"`: a concurrent agent raced you; re-query via `pharaoh-context-gather`, adopt the existing spelling, rewrite your draft to match.

### Step 4: Resolve tailoring (type + emit mode)

Read `<project_root>/ubproject.toml` and `<project_root>/pharaoh.toml`.

**Type resolution:** find `[[needs.types]]` entry where `directive == target_level`. Extract `prefix`. If not declared:
- `on_missing_config == "fail"` → FAIL.
- `on_missing_config == "prompt"` → emit `{status: "needs_confirmation", proposal: ...}` and return without emitting reqs.
- `on_missing_config == "use_default"` → use `<target_level>__` silently.

**Emit mode:** per the Tailoring awareness order. Log the resolved mode on the header line.

**Codelinks format** (only if `emit == "codelinks_comment"`): resolve `[codelinks.projects.<name>.analyse.oneline_comment_style]` via `codelinks_project_name` or by matching `file_path` against each project's `source_discover.src_dir`. Zero or multiple matches with `on_missing_config != "fail"` → `needs_confirmation`. `on_missing_config == "fail"` → FAIL.

### Step 5a: Emit — `rst` mode

For each boundary-observable behavior (per Rule 5 enumeration):

- `<short_title>` — 3-6 word summary.
- `:id: <id_prefix><filename_stem>_<n>` — `<id_prefix>` resolved in Step 4. File basename (stem, snake_case) as disambiguator. Examples: `comp_req__csv2needs_01`, `CREQ_csv2needs_01`.
- `:status: draft`.
- `:satisfies: <parent_1>, ...` — iff `parent_feat_ids` non-empty. All parents comma-joined. If `[[needs.extra_links]]` declares a different outgoing name (e.g. `realizes`), use that instead.
- `:source_doc: <path to implementing source file>` — per Rule 3.
- `:verification: tc__TBD` — per Rule 6.
- Body — single shall clause, component subject (Rule 1), no internals (Rule 2), adds constraint (Rule 4), atomicity + no conjunctions (Atomicity rule above). Canonical names from Steps 1/3.

### Step 5b: Emit — `codelinks_comment` mode

For each behavior, emit one line that sphinx-codelinks' oneline parser would read back into a need equivalent to what `rst` mode would produce. Follow tailored `needs_fields` order and escape rules. Do NOT include the language comment prefix — that is `pharaoh-req-codelink-annotate`'s concern.

The `links` field renders as `[<parent_1>, ...]` when `parent_feat_ids` non-empty, else `[]` (or omitted if tailored `default = []`). The body shall-clause does NOT fit on a one-line comment — implied by the title and lost in this mode. For full shall-clause text use `emit="rst"`.

Target: 1-5 reqs per file (per split_strategy). Fewer than 1 only if the file has no observable behavior; more than 5 suggests over-decomposition.

### Step 6: Return

Concatenation of directive blocks with blank-line separators. No prose wrapper, no final summary.

## Failure modes

- `file_path` not readable → return empty output (no reqs).
- `pharaoh-context-gather` errors → log and proceed as if no match found.
- `pharaoh-decision-record` returns `"error"` (not `"duplicate"`) → log and proceed. Do not retry.

## Composition

Under `pharaoh-execute-plan`, a plan emitted by `pharaoh-write-plan` dispatches N instances of this skill via a `foreach` task over the file list. Per-CREQ review is scheduled as explicit top-level `review_comp_reqs` + `grounding_check_comp_reqs` + `api_coverage_comp_reqs` plan tasks (see `pharaoh-write-plan` templates); the plan DAG enforces them as dependencies of `quality_gate`. Direct out-of-plan invocation by a human auditor is acceptable; the caller is responsible for running the sibling reviews if coverage matters.

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` reading the explicit plan-task output files.

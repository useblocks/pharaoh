---
name: pharaoh-feat-draft-from-docs
description: Use when reading one or more existing documentation files (unstructured prose, README, tutorial) and emitting one or more feature-level RST directives (typed by `target_level`, default `feat`) that describe the user-facing capabilities documented in those files. Does NOT read source code. Does NOT emit component requirements. Does NOT map features to files — that is `pharaoh-feat-file-map`.
---

# pharaoh-feat-draft-from-docs

## When to use

Invoke when a project has unstructured documentation (e.g. `docs/source/features/*.rst`, `README.md`, product overview pages) that describes user-facing capabilities in prose, and you need to extract those capabilities as sphinx-needs `feat` (or equivalent) directives. This is the first step of reverse-engineering a requirements model from an existing project: docs → features. The follow-up skill `pharaoh-feat-file-map` maps each emitted feature to source files; `pharaoh-req-from-code` then generates component requirements per-file from code.

Do NOT use to draft features from scratch (that is `pharaoh-req-draft` with `target_level="feat"`). Do NOT use to emit reqs from code (that is `pharaoh-req-from-code`). Do NOT use to generate architecture diagrams (a separate future skill).

## Tailoring awareness

The emitted directive name and ID prefix come from the consumer project's `ubproject.toml` `[[needs.types]]` (or `.pharaoh/project/id-conventions.yaml` if present). The caller passes `target_level` — use it verbatim as the directive name. Do NOT hardcode `feat` as the only acceptable type. Projects may call their top-level artefact `story`, `capability`, `feature`, `use_case`, etc.

## Atomicity

- (a) Indivisible — one invocation reads `doc_files` and emits N feature directives. No source-code reads. No file-mapping. No inter-feature dependency analysis. One artefact × one phase.
- (b) Input: `{doc_files: list[str], target_level: str, project_root: str, papyrus_workspace?: str, reporter_id: str, on_missing_config?: "fail"|"prompt"|"use_default"}`. Output: single JSON object `{"feats": [{"id", "title", "type", "body", "source_doc", "raw_rst"}, ...]}`. The `raw_rst` field of each feat is the full RST directive block; downstream skills that want raw RST read it from there. On `on_missing_config="prompt"` with `target_level` undeclared → single JSON object `{status: "needs_confirmation", proposal: ...}`.
- (c) Reward: deterministic fixture — a 2-file doc tree with known feature vocabulary (e.g. `features/csv.rst` mentioning "CSV import" and "CSV export"; `features/jama.rst` mentioning "Jama pull" and "Jama push"). After skill runs, scorer checks:
  1. Every emitted block uses `target_level` as the directive name.
  2. Every emitted block has a `:id:` option.
  3. Every emitted ID prefix equals the ID prefix resolved from the project's tailoring (see Output).
  4. Every emitted block contains a `:source_doc:` option pointing to one of the `doc_files` paths.
  5. For each fixture doc paragraph marked as "must_yield_feat" in the fixture metadata, at least one emitted block's title or body mentions the paragraph's canonical vocabulary (substring match, case-insensitive).
  6. At least 1 feat is emitted (non-empty output).

  Pass = all 6 checks pass.
- (d) Reusable: any reverse-engineering workflow on projects with existing prose docs; migration from README-only to sphinx-needs; extracting features from product specs.
- (e) Composable: strictly one phase (docs → feat directives). Never invokes `pharaoh-req-from-code`, `pharaoh-arch-draft`, or `pharaoh-feat-file-map`. A plan emitted by `pharaoh-write-plan` composes this skill with `pharaoh-feat-file-map` and downstream req-emission tasks — not vice versa.

## Input

- `doc_files`: list of absolute paths to documentation files to read. Typically `.rst`, `.md`, or `.txt`. At least one must be provided. Files are read but not modified.
- `target_level`: directive name for the emitted features. Must match a `[[needs.types]].directive` in the consumer project's `ubproject.toml` (e.g. `"feat"`, `"story"`, `"capability"`). The emitted directive uses this name verbatim.
- `project_root`: absolute path to the consumer project's root, used to resolve the ID prefix from `ubproject.toml` (`[[needs.types]]` entry whose `directive` equals `target_level`). If the `ubproject.toml` does not declare a prefix for `target_level`, fall back to `<target_level>__` (double-underscore convention).
- `papyrus_workspace` (optional): path to `.papyrus/` directory for canonical-term coordination with concurrent agents. If omitted, the skill operates in no-memory mode.
- `reporter_id`: short identifier for this agent (e.g. `feat-draft-from-docs:features`). Passed to `pharaoh-decision-record` calls.
- `granularity` (optional): `"doc" | "top_section" | "manual_hint"`. Default `"doc"`. Controls decomposition of each doc file into feats:
  - `"doc"` — one feat per input doc file. Simplest; right for "one topic per doc" layouts. Current default and the shape that has been stable since initial dogfooding.
  - `"top_section"` — split each doc at its top-level headings (RST: title underlined with `===`; Markdown: a line starting with a single `#`). Emit one feat per top-level section. Right for docs that cover multiple capabilities under one roof (e.g. a ReqIF connector doc that covers both export and import — granularity `top_section` produces `FEAT_reqif_export` + `FEAT_reqif_import` instead of a single fused `FEAT_reqif_exchange`).
  - `"manual_hint"` — look for explicit split markers inside each doc: `.. feat-split::` comment-directive (RST) or `<!-- feat-split -->` marker (Markdown). Emit one feat per segment separated by those markers. Caller-controlled; useful when prose organisation does not match the desired feat boundary.
- `on_missing_config` (optional): `"fail" | "prompt" | "use_default"`. Default `"prompt"`. Determines behavior when `target_level` is not declared in `ubproject.toml`. See shared `check → propose → confirm` pattern in `shared/diagram-tailoring.md` (same semantics, different subject matter).

## Output

A single JSON object with one top-level key `feats` (list of feat objects). One feat object per emitted feature. Shape:

```json
{
  "feats": [
    {
      "id": "<id_prefix><snake_case_id>",
      "title": "<short_title>",
      "type": "<target_level>",
      "body": "<one-sentence feature statement in user-facing language>",
      "source_doc": "<relative_path_to_doc_file>",
      "raw_rst": ".. <target_level>:: <short_title>\n   :id: ...\n   :status: draft\n   :source_doc: ...\n\n   <body>\n"
    }
  ]
}
```

The `raw_rst` field MUST be exactly the directive block as it would appear if pasted into an RST file. Downstream skills (e.g. `pharaoh-req-review`, `pharaoh-feat-review`) read `raw_rst` when they need the directive text; helpers that consume `feats` (e.g. `to_papyrus_seeds`) read `id`, `title`, `body`.

`<id_prefix>` resolution:
1. Read `<project_root>/ubproject.toml`.
2. Find the `[[needs.types]]` entry whose `directive` equals `target_level`.
3. If it has a `prefix` field, use that verbatim (e.g. `prefix = "FEAT_"` → `FEAT_csv_import`).
4. Otherwise use `<target_level>__` (e.g. `feat__csv_import`).

`<snake_case_id>` is derived from the feature's short_title (lowercase, spaces → underscores, non-alphanumeric stripped).

`source_doc` — relative path (from `project_root`) to the doc file this feature was derived from. This is a Pharaoh convention for provenance. `pharaoh-bootstrap` declares `source_doc` under `[[needs.extra_options]]` by default so sphinx-needs does not warn under `-nW`; callers who opted out of the default must declare it manually or accept the warnings. Downstream skills (`pharaoh-feat-file-map`, plans emitted by `pharaoh-write-plan`) read this to group features by source doc.

The output is one JSON object — no surrounding prose, no concatenated RST outside the JSON.

## Output schema

Validated as `json_obj` by `pharaoh-output-validate`. Validator checks:
1. Top-level is a JSON object with exactly one required key `feats` (list).
2. Every `feats[*]` has the keys `id`, `title`, `type`, `body`, `source_doc`, `raw_rst`.
3. `feats[*].type` equals input `target_level` (default `feat`).
4. `feats[*].source_doc` references a path present in the input `doc_files` list.
5. `feats[*].raw_rst` matches the RST directive Stage 1 + Stage 2 regex from `pharaoh-req-from-code` `## Output schema`, with directive name = `feats[*].type` and `:id:` / `:status:` / `:source_doc:` options present.
6. `feats[*].id` matches the resolved `<id_prefix><snake_case_id>` pattern.

## Process

### Step 1: MANDATORY — query Papyrus for canonical feature names (if workspace provided)

For each feature concept you identify in the docs, query `pharaoh-context-gather` with a semantic description ("the capability that exports needs to CSV"). If a canonical feature name already exists, reuse it verbatim. This prevents drift when the same doc is re-processed or when multiple docs describe overlapping capabilities.

Skip this step if `papyrus_workspace` is not provided (no-memory mode).

### Step 2: Read all doc_files

Read every file in `doc_files`. Concatenate into working memory. Identify user-facing capability boundaries:

- Section headers often signal capability boundaries ("## Import from ReqIF", "## Export to Jama").
- Imperative verbs describing what users can do with the product ("You can import …", "Users can export …").
- Top-level bullet lists in README "Features" sections.
- sphinx-design cards with short capability labels.

Ignore:
- Installation/setup instructions.
- Contributing guidelines.
- License text.
- Changelog entries.

### Step 3: Resolve ID prefix from tailoring (with check → propose → confirm)

Read `<project_root>/ubproject.toml`. Find the `[[needs.types]]` entry matching `target_level`. Extract its `prefix` field. Three resolution paths:

1. **Type declared, prefix present** → use the declared prefix. Proceed.
2. **Type declared, prefix absent** → use `<target_level>__` silently (this is a minor-enough gap to default).
3. **Type NOT declared**, OR `ubproject.toml` missing entirely → branch on `on_missing_config`:
   - `"fail"` → FAIL with: `"target_level=<value> not declared in <project_root>/ubproject.toml. Run pharaoh-bootstrap first, or pass on_missing_config='prompt' to negotiate."`
   - `"prompt"` (default) → emit a `needs_confirmation` proposal:
     ```json
     {
       "status": "needs_confirmation",
       "proposal": {
         "target_level": "<value>",
         "proposed_prefix": "<uppercase value>_",
         "rationale": "target_level is not declared as a type in ubproject.toml. Propose adding it so downstream skills have a stable type.",
         "tailoring_patch": {
           "target_file": "ubproject.toml",
           "table": "[[needs.types]]",
           "entry": {"directive": "<value>", "title": "<Title Case value>", "prefix": "<uppercase>_"}
         }
       }
     }
     ```
     Return without emitting features. The caller confirms, runs `pharaoh-tailor-fill` or edits manually, then re-invokes with `on_missing_config="use_default"`.
   - `"use_default"` → synthesize defaults silently: treat `target_level` as declared with prefix `<target_level>__`. Proceed.

### Step 4: Record newly surfaced canonical feature names in Papyrus

Only if `papyrus_workspace` is provided. For each feature concept you will emit that was NOT returned by Step 1, invoke `pharaoh-decision-record` with:

- `type`: `"fact"`
- `canonical_name`: the short_title you chose for this feature (space-separated, Title Case — e.g. `"CSV Import"`)
- `body`: one sentence describing the capability
- `reporter_id`: your `reporter_id` input
- `tags`: `["origin:feat-draft-from-docs", "doc:<doc_basename>"]`

If `pharaoh-decision-record` returns `"duplicate"`, re-query and adopt the existing canonical name.

### Step 5: Emit feature directives

The set of emitted capabilities depends on `granularity`:

- `"doc"` (default): one feat per input doc file. If a doc covers multiple topics, pick the dominant theme for the title/body and rely on downstream skills (e.g. `pharaoh-feat-balance`) to flag under-decomposition.
- `"top_section"`: enumerate top-level headings across all input docs. For RST, a top-level heading is a line followed by a line of `=` characters of matching length. For Markdown, a top-level heading is a line starting with `# ` (single hash, not `##`). Each top-level section becomes one feat; the section's prose is the body source. A doc with no top-level headings falls back to one feat for the whole doc (same as `"doc"`).
- `"manual_hint"`: scan each doc for split markers. RST: lines of form `.. feat-split::` (optionally followed by a feat title on the same line, e.g. `.. feat-split:: CSV Import`). Markdown: lines exactly matching `<!-- feat-split -->` or `<!-- feat-split: Title -->`. Segments between markers (and the implicit segment before the first marker, if any) each become one feat. A doc with zero markers falls back to one feat for the whole doc.

Emit one block per the Output shape per resolved capability. Target: 3-15 features total across all `doc_files`. Fewer than 3 suggests under-decomposition (lumping); more than 15 suggests over-decomposition (every button becomes a feature). If you hit these bounds, log a warning and proceed anyway — the eval will flag it.

Body text must be user-facing: "The system shall import needs from ReqIF files", not "The `from_reqif` command parses XML via lxml". Implementation detail belongs in `comp_req`, not `feat`.

### Step 6: Return

Emit one JSON object `{"feats": [...]}` per the Output shape. For each emitted capability build the per-feat mapping with `id`, `title`, `type` (= `target_level`), `body`, `source_doc`, and `raw_rst` (the literal RST block that would render the directive). Nothing else on stdout — no prose wrapper, no fenced code block.

## No-memory mode

If `papyrus_workspace` is absent, skip Steps 1 and 4. Proceed directly to 2, 3, 5, 6.

## Failure modes

- `doc_files` empty → FAIL: "At least one doc file required."
- Any file in `doc_files` unreadable → log and skip that file; do not abort unless all files are unreadable.
- `ubproject.toml` missing or `target_level` undeclared → FAIL per Step 3.
- `pharaoh-context-gather` / `pharaoh-decision-record` errors → log and proceed as if no match (never abort on memory-layer issues).

## Last step

After emitting the artefact, invoke `pharaoh-feat-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must regenerate (via `pharaoh-feat-regenerate` if available, or by re-invoking this skill with the findings as input).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

## Composition

A plan emitted by `pharaoh-write-plan` calls this skill once with the full `doc_files` list in the initial wave, then a foreach task dispatches `pharaoh-feat-file-map` once per emitted feature to produce the feat→files mapping.

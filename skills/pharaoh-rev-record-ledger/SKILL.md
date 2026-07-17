---
name: pharaoh-rev-record-ledger
description: Use when a recovery emission from `pharaoh-req-from-code`, `pharaoh-rev-cluster-synthesize`, or `pharaoh-rev-atomicity-split` is ready to persist into the project's needs corpus. Wraps the emission into the engine's `RecoveryResult` shape, applies any pending cluster member up-links, writes it to a temp file, and runs `ubc agent reverse record --input <tempfile>` -- the only skill in the tree allowed to shell out to that command. Returns the CLI's JSON stdout unchanged.
---

# pharaoh-rev-record-ledger

## When to use

Invoke as the terminal write step of a reverse-recovery plan task chain, after the rung's recovery skill(s) have emitted `reqs` (`pharaoh-req-from-code` at an extraction rung, `pharaoh-rev-cluster-synthesize` then `pharaoh-rev-atomicity-split` at a synthesis rung) and, when the emission has concrete per-file anchors, `pharaoh-req-codelink-annotate` has run. `pharaoh-execute-plan/schema.md`'s Non-goals forbid a bare shell-out task (`skill:` must resolve to a real skill directory) -- this skill exists so a plan-DAG task can reach `ubc agent reverse record` at all.

Do NOT use to draft, cluster, split, or annotate a need -- those are upstream. Do NOT use to read the corpus for any purpose other than resolving a cluster's pre-existing lower-rung members named in `member_uplinks` -- that read is Tier 1 of `shared/data-access.md`, not a new responsibility. Do NOT invoke more than once per recovery emission. A plan with N files or N clusters invokes this skill N times, one per emission, not once with a hand-merged combined list (`plan.yaml`'s ref grammar disallows list-concatenation across sibling producer tasks -- see `pharaoh-write-plan/templates/reverse-engineer-project.yaml.j2`'s per-diagram-kind review split for the same constraint).

## Atomicity

- (a) Indivisible -- one recovery emission (`reqs` plus provenance) in, one CLI record call out. No drafting, no clustering, no splitting, no annotation. The one exception folded into this atom, not a second responsibility: resolving and patching the up-link field on the emission's cluster members, because that resolution only exists to build the single `RecoveryResult` payload this call sends -- it is not a general-purpose need lookup.
- (b) Input: `{reqs: list[dict], member_uplinks?: {link_field: str, links: [{member_id, target_id}]}, source_span_lines?: list[int|null], source_path: str, target_rst: str, run: {agent, model, prompt_hash, sources}, project_root: str}`. Output: single JSON object -- the CLI's stdout, parsed and returned verbatim.
- (c) Reward: fixture `fixtures/basic/{input-result.json, expected-output.json}`. Given `input-result.json` (one synthesized `feat` need plus `member_uplinks` over three pre-existing `comp_req` members, continuing the CSV-export fixture used across the `rev-*` family), the wrapped `RecoveryResult` this skill would send to `ubc agent reverse record` must (a) rename `reqs` -> `needs`, (b) carry one `needs[]` entry per input req with `id`/`type`/`body` unchanged and every other native field on that req passed through, (c) carry one additional `needs[]` entry per `member_uplinks.links` entry, with its resolved `link_field` value extended by `target_id` (deduplicated, existing order preserved) and every other pre-existing field on that member untouched, and (d) this skill's own return must equal `expected-output.json` verbatim (the mocked CLI stdout). `ubc agent reverse record` itself is Task 10's engine surface, outside this worktree -- the fixture documents the wrap and the pass-through contract, not the binary's internals.
- (d) Reusable across the whole `rev-*` family, and by any future recovery skill that emits the native `{reqs: [...]}` shape -- the wrap step only reads `id`/`type`/`body` plus whatever else is present, it does not assume a specific emitter.
- (e) Composable -- strictly the terminal persistence step. Never invoked mid-chain, never invokes another Pharaoh skill, never invoked twice for the same emission (idempotence of the underlying `ubc agent reverse record` call is the engine's concern, not this skill's).

## Input

- `reqs`: list of req objects in the native shape emitted by `pharaoh-req-from-code` / `pharaoh-rev-cluster-synthesize` / `pharaoh-rev-atomicity-split`. Every entry carries at least `id`, `type`, `body`, and commonly also `title`, `satisfies` (or the project's tailored up-link field name), `source_doc`, `verification`, `raw_rst`, and family-specific fields (`intent_refs`, `intent_gap`, `cluster_id` from cluster-synthesize, or `status`, `split_from` from atomicity-split). Must be non-empty.
- `member_uplinks` (optional): `{link_field: str, links: [{member_id: str, target_id: str}, ...]}`, exactly the shape `pharaoh-rev-cluster-synthesize` emits. Present only at a synthesis rung, after its cluster's members already exist in the corpus (written by an earlier extraction-rung ledger call). Absent at an extraction rung -- `pharaoh-req-from-code` never emits `member_uplinks`.
- `source_span_lines` (optional): list of `int | null`, order-aligned with `reqs`, taken from `pharaoh-req-codelink-annotate`'s `inserted_line` output for the same items. When present and the same length as `reqs`, populates each corresponding need's `source_span` as `{file: source_path, line: source_span_lines[i]}`. Omit at rungs where the emission has no single-file anchor (e.g. a synthesized or split need with no one-line-in-one-file grounding).
- `source_path`: path (relative to `project_root`) of the source artefact this emission traces to -- the file scanned at an extraction rung, or the synthesis scope (e.g. the target module) at a synthesis rung.
- `target_rst`: path (relative to `project_root`) of the RST file the recovered needs should render into.
- `run`: `{agent: str, model: str, prompt_hash: str, sources: list[str]}` -- provenance block. `agent` identifies this invocation (e.g. `"rev-record-ledger:<stem_or_cluster_id>"`), `model` the model id that produced the emission, `prompt_hash` a stable hash of the skill + inputs the caller supplies (e.g. from `pharaoh-execute-plan`'s dispatch record), `sources` the list of source file paths the emission was grounded in.
- `project_root`: absolute path. Used as the `ubc` invocation's working directory and, when `member_uplinks` is present, to resolve member need objects via Tier 1.

## Output

A single JSON object: the CLI's stdout, parsed via `json.loads` and returned unchanged -- this skill does not re-wrap, rename, or filter it. The response envelope itself is owned by the engine (`ubc agent reverse record`, Task 10), not by Pharaoh. `fixtures/basic/expected-output.json` documents Pharaoh's current best-known shape (a status field plus the ids written and updated) as an illustrative example, not a guarantee -- treat additional or renamed fields as forward-compatible. The one contract this skill enforces is "exit 0 and a JSON object on stdout". See Output schema and Last step.

## Output schema

Validated as `json_obj` by `pharaoh-output-validate` with `schema_context: {required_keys: [], allowed_unknown_keys: true}`. Deliberately minimal: the top level must parse as a JSON object, and this skill does not assert specific keys inside it, because the exact shape is engine-owned and evolving on the Task 10 side, not a Pharaoh-authored schema.

## Process

### Step 1: Validate the emission

`reqs` must be a non-empty list. `source_path`, `target_rst`, `run`, and `project_root` must all be present. FAIL per Failure modes if not.

### Step 2: Resolve and patch member up-links (only if `member_uplinks` is present)

For each entry in `member_uplinks.links`, resolve the full existing need object for `member_id` via `ubc build needs --format json` (`shared/data-access.md` Tier 1). This is a write-path skill, so there is no Tier 2/3 fallback for the write itself (see Failure modes), but the *read* half of this step follows the same Tier-1-first discipline `shared/data-access.md` establishes for its read commands -- check `ubc --version`, run from `project_root`, parse the JSON stdout directly -- falling through to Tier 2 (ubCode MCP) then Tier 3 (raw file parsing) per that document if `ubc` itself is unavailable for the read.

For each resolved member:

1. Read its current value of `member_uplinks.link_field` (empty list if the field is absent).
2. Extend it with `target_id`, deduplicated, existing order preserved, `target_id` appended if new.
3. Stage one `needs[]` update entry: the member's full existing need object, unchanged except for the extended `link_field` value. Carrying the whole object forward (not a bare `{id, link_field}` patch) is deliberate -- whether `ubc agent reverse record` merges or replaces by id is an engine-internal decision this skill does not assume either way, so nothing the member already had is put at risk of being dropped.

A `member_id` that does not resolve on any tier is logged as a warning and skipped -- it does not abort the whole ledger write (unlike `pharaoh-rev-cluster-synthesize`'s own >=2-resolvable floor, an unresolved member up-link here does not block persisting the emission's own `reqs`, since those are unaffected by the failure).

### Step 3: Build the `needs[]` array

For each item in `reqs`, in order: `{id, type, body}` plus every other field already present on that item, passed through verbatim (`satisfies` / the tailored up-link field, `source_doc`, `verification`, `title`, `status`, `split_from`, `cluster_id`, `intent_refs`, `intent_gap`, `confidence` when present). If `source_span_lines` is provided and its length equals `len(reqs)`, add `source_span: {file: source_path, line: source_span_lines[i]}` to the i-th entry (skip the field for any index whose `source_span_lines[i]` is `null`).

Append the member-update entries staged in Step 2, if any.

### Step 4: Wrap into `RecoveryResult`

```json
{
  "source_path": "<source_path>",
  "target_rst": "<target_rst>",
  "run": {"agent": "...", "model": "...", "prompt_hash": "...", "sources": ["..."]},
  "needs": [/* Step 3 array */]
}
```

This is the `reqs` -> `needs` adapter the engine's `record` verb expects.

### Step 5: Write the temp file

Write the `RecoveryResult` JSON to a temp file. Prefer `<workspace_dir>/rev-record-ledger-<run.agent-sanitized>.json` when a plan workspace is available, otherwise use a process-local temp file. The path must be stable for the duration of this single invocation only -- no cleanup contract beyond the invocation, the executor's workspace retention policy owns lifecycle.

### Step 6: Shell out to the CLI

Per `shared/data-access.md` Tier 1 discipline: first confirm `ubc --version` exits 0. Then, from `project_root`, run:

```
ubc agent reverse record --input <tempfile>
```

Capture stdout, stderr, and exit code. This command is a write, not one of the read commands `shared/data-access.md`'s Tier 1 table lists (`ubc build needs`, `ubc config`, `ubc check`, `ubc schema validate`, `ubc diff`) -- it follows the same Tier-1-first, run-from-project-root, parse-JSON-directly discipline that table establishes, and this skill is the only place in the skill tree permitted to invoke it (see `pharaoh-rev-cluster-synthesize` and `pharaoh-rev-atomicity-split`, both of which explicitly defer to this skill for the CLI call).

### Step 7: Return

On exit 0: parse stdout as JSON (FAIL if it does not parse) and return it verbatim as this skill's output. On non-zero exit: FAIL per Failure modes, naming stderr's first line. Do not retry, do not fabricate a success response.

## Failure modes

- `reqs` empty, or `source_path` / `target_rst` / `run` / `project_root` missing -> FAIL: `"pharaoh-rev-record-ledger: missing required input <name>"`.
- `ubc --version` non-zero exit (CLI unavailable) -> FAIL: `"ubc CLI not available. pharaoh-rev-record-ledger has no Tier 2/3 fallback for the write path -- ubCode MCP and raw file parsing are read-only per shared/data-access.md."`
- A `member_uplinks.links[*].member_id` unresolved on any tier -> log a warning naming the id, skip that member's update entry, proceed (not fatal).
- Temp file write failure -> FAIL: `"pharaoh-rev-record-ledger: could not write temp file <path>"`.
- `ubc agent reverse record` non-zero exit -> FAIL: `"ubc agent reverse record failed: <stderr first line>"`. No retry.
- CLI stdout does not parse as JSON despite exit 0 -> FAIL: `"ubc agent reverse record returned non-JSON stdout"`.

## Last step

After the CLI call returns, invoke `pharaoh-output-validate` on the raw stdout: `mode: "block"`, `target_schema: "json_obj"`, `output_text: <raw CLI stdout>`, `schema_context: {required_keys: [], allowed_unknown_keys: true}`. Attach the returned validation JSON to this skill's output under `review`. If `valid` is `false`, return a non-success status with the validation findings verbatim and do NOT report the ledger write as complete -- the caller inspects the CLI's stderr and re-invokes this skill once the underlying issue (a malformed `RecoveryResult`, or a CLI-side fault) is fixed. There is no dedicated `*-regenerate` skill for this step: the wrap in Steps 2-4 is deterministic, so a validation failure here points at the CLI response or this skill's own wrap, never at requirement content -- content quality was already reviewed upstream, at each rung's own emission Last step (`pharaoh-rev-cluster-synthesize` -> `pharaoh-feat-review`, `pharaoh-rev-atomicity-split` -> `pharaoh-req-review`, or the plan-level `review_*` / `grounding_*` tasks for `pharaoh-req-from-code`). This step checks only whether the persistence call itself succeeded and returned a well-shaped response -- structural, not prose-quality, the same distinction `pharaoh-req-codelink-annotate`'s Last step draws for its own one-line insert.

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

## Composition

The terminal write task of a reverse-recovery plan chain: `pharaoh-write-plan`'s `reverse-recover-rung` template dispatches one instance of this skill per file (extraction rung) or per cluster (synthesis rung), each `depends_on` that item's own emission (and, where applicable, its `pharaoh-req-codelink-annotate` task). This skill never fans out itself -- the plan's per-item unrolling is what produces N calls for N emissions. After this skill returns, the terminal `pharaoh-quality-gate` task depends on every `record_ledger_*` instance alongside the review and grounding tasks, so a plan cannot report success while a ledger write silently failed.

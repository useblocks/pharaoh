---
name: pharaoh-rev-record-ledger
description: Use when a recovery emission from `pharaoh-req-from-code`, `pharaoh-rev-cluster-synthesize`, or `pharaoh-rev-atomicity-split` is ready to persist into the project's advisory ledger. Wraps the emission into the engine's `RecoveryResult` shape (`reqs` -> `needs`, matching `RecoveredNeed`), writes it to a temp file, and runs `ubc agent reverse record --input <tempfile>` -- the only skill in the tree allowed to shell out to that command. `record` is the ledger's only writer and never touches RST. It does not apply cluster member up-links -- those are authored directly into RST by `pharaoh-rev-cluster-synthesize` (see that skill's `member_updates` output). Returns the CLI's JSON stdout unchanged.
---

# pharaoh-rev-record-ledger

## When to use

Invoke as the terminal write step of a reverse-recovery plan task chain, after the rung's recovery skill(s) have emitted `reqs` (`pharaoh-req-from-code` at an extraction rung, `pharaoh-rev-cluster-synthesize` then `pharaoh-rev-atomicity-split` at a synthesis rung) and, when the emission has concrete per-file anchors, `pharaoh-req-codelink-annotate` has run. `pharaoh-execute-plan/schema.md`'s Non-goals forbid a bare shell-out task (`skill:` must resolve to a real skill directory) -- this skill exists so a plan-DAG task can reach `ubc agent reverse record` at all.

Do NOT use to draft, cluster, split, or annotate a need -- those are upstream. Do NOT use to author or edit RST -- this skill only ever writes the ledger. It never reads the corpus and never patches a member need's up-link field (that RST edit is authored by `pharaoh-rev-cluster-synthesize` itself, in `member_updates`, and persisted the same way any other skill-emitted `raw_rst` is persisted). Do NOT invoke more than once per recovery emission. A plan with N files or N clusters invokes this skill N times, one per emission, not once with a hand-merged combined list (`plan.yaml`'s ref grammar disallows list-concatenation across sibling producer tasks -- see `pharaoh-write-plan/templates/reverse-engineer-project.yaml.j2`'s per-diagram-kind review split for the same constraint).

## Atomicity

- (a) Indivisible -- one recovery emission (`reqs` plus provenance) in, one CLI record call out. No drafting, no clustering, no splitting, no annotation, no RST edit of any kind -- this skill writes the ledger only, per the engine's `record` module contract (it never reads or writes RST). Member up-link patching lives in `pharaoh-rev-cluster-synthesize` (its `member_updates` output), the skill that actually authors RST in this family.
- (b) Input: `{reqs: list[dict], source_spans?: list[[int, int]|null], source_path: str, target_rst: str, run: {agent, model, prompt_hash, sources}, project_root: str}`. Output: single JSON object -- the CLI's stdout, parsed and returned verbatim.
- (c) Reward: two deterministic fixtures.

  **`fixtures/basic`** -- `input-result.json` (one synthesized `feat` need, continuing the CSV-export fixture used across the `rev-*` family, with `source_spans: null`, since a synthesized need has no single element to anchor). The wrapped `RecoveryResult` this skill would send to `ubc agent reverse record` must (a) rename `reqs` -> `needs`, (b) carry exactly one `needs[]` entry with `id`/`type`/`body` unchanged and every other native field on the req passed through, unchanged, (c) carry no other entries -- this skill never adds a members entry, member up-links are not its concern -- and (d) this skill's own return must equal `expected-output.json` verbatim (the mocked CLI stdout, `{"shard_path": "...", "need_count": 1}` -- the engine's `RecordOutcome` shape, see Output).

  **`fixtures/real-source-span`** -- `input-result.json` carries two `comp_req` reqs from an extraction rung plus `source_spans: [[11, 18], null]`. `expected-recovery-result.json` is the exact wrapped `RecoveryResult` this skill builds: `needs[0].source_span == [11, 18]` (a two-element array, matching the engine's `RecoveredNeed.source_span: Option<[u32; 2]>`), `needs[1]` carries no `source_span` key at all (`null` in, key omitted out, so it deserializes to `None` rather than a JSON `null`). `expected-output.json` is the mocked CLI stdout.

  `ubc agent reverse record` itself is Task 10's engine surface, outside this worktree -- the fixtures document the wrap and the pass-through contract, not the binary's internals.
- (d) Reusable across the whole `rev-*` family, and by any future recovery skill that emits the native `{reqs: [...]}` shape -- the wrap step only reads `id`/`type`/`body` plus whatever else is present, it does not assume a specific emitter.
- (e) Composable -- strictly the terminal persistence step. Never invoked mid-chain, never invokes another Pharaoh skill, never invoked twice for the same emission (idempotence of the underlying `ubc agent reverse record` call is the engine's concern, not this skill's).

## Input

- `reqs`: list of req objects in the native shape emitted by `pharaoh-req-from-code` / `pharaoh-rev-cluster-synthesize` / `pharaoh-rev-atomicity-split`. Every entry carries at least `id`, `type`, `body`, and commonly also `title`, `satisfies` (or the project's tailored up-link field name), `source_doc`, `verification`, `raw_rst`, and family-specific fields (`intent_refs`, `intent_gap`, `cluster_id` from cluster-synthesize, or `status`, `split_from` from atomicity-split). Must be non-empty. Never includes a cluster's member needs -- `pharaoh-rev-cluster-synthesize` authors those directly into RST as `member_updates`, this skill never sees them.
- `source_spans` (optional): list of `[start_line, end_line] | null`, order-aligned with `reqs`. Each non-null entry is a 0-based inclusive line range of the CODE ELEMENT the requirement traces to, mirroring the engine's `CodelinkSourceMap.line_range` / the `src-trace` directive's own source-map convention -- NOT the annotation insertion line `pharaoh-req-codelink-annotate` reports. `pharaoh-req-codelink-annotate`'s `inserted_line` is a single int marking where the *comment* was inserted, not the element's range, and MUST NOT be wired into this field: a caller with only an insertion line available omits `source_spans` (or leaves that index `null`) rather than fabricate a range. When present and the same length as `reqs`, populates the i-th need's `source_span` with `source_spans[i]` verbatim, as a two-element array, matching the engine's `RecoveredNeed.source_span: Option<[u32; 2]>`. Omit the field entirely, or leave an index `null`, at rungs / items where no real element range is available (e.g. a synthesized or split need with no one-line-in-one-file grounding, or an extraction-rung item where only the codelink comment's insertion line was resolved).
- `source_path`: path (relative to `project_root`) of the source artefact this emission traces to -- the file scanned at an extraction rung, or the synthesis scope (e.g. the target module) at a synthesis rung.
- `target_rst`: path (relative to `project_root`) of the RST file the recovered needs should render into.
- `run`: `{agent: str, model: str, prompt_hash: str, sources: list[str]}` -- provenance block. `agent` identifies this invocation (e.g. `"rev-record-ledger:<stem_or_cluster_id>"`), `model` the model id that produced the emission, `prompt_hash` a stable hash of the skill + inputs the caller supplies (e.g. from `pharaoh-execute-plan`'s dispatch record), `sources` the list of source file paths the emission was grounded in.
- `project_root`: absolute path. Used only as the `ubc` invocation's working directory -- this skill never reads the corpus, so `project_root` has no other role.

## Output

A single JSON object: the CLI's stdout, parsed via `json.loads` and returned unchanged -- this skill does not re-wrap, rename, or filter it. The response envelope itself is owned by the engine (`ubc agent reverse record`, Task 10), not by Pharaoh. `fixtures/basic/expected-output.json` documents the engine's actual `RecordOutcome` shape (`ubc_agent::reverse::record::RecordOutcome`, serialized as-is by the CLI): `{"shard_path": "<absolute path to the written ledger shard>", "need_count": <int>}` -- not a guess or a placeholder, but still treat additional or renamed fields as forward-compatible should the engine grow the struct. The one contract this skill enforces is "exit 0 and a JSON object on stdout". See Output schema and Last step.

## Output schema

Validated as `json_obj` by `pharaoh-output-validate` with `schema_context: {required_keys: [], allowed_unknown_keys: true}`. Deliberately minimal: the top level must parse as a JSON object, and this skill does not assert specific keys inside it, because the exact shape is engine-owned and evolving on the Task 10 side, not a Pharaoh-authored schema.

## Process

### Step 1: Validate the emission

`reqs` must be a non-empty list. `source_path`, `target_rst`, `run`, and `project_root` must all be present. FAIL per Failure modes if not.

### Step 2: Build the `needs[]` array

For each item in `reqs`, in order: `{id, type, body}` plus every other field already present on that item, passed through verbatim (`satisfies` / the tailored up-link field, `source_doc`, `verification`, `title`, `status`, `split_from`, `cluster_id`, `intent_refs`, `intent_gap`, `confidence` when present). If `source_spans` is provided and its length equals `len(reqs)`, and `source_spans[i]` is non-null, add `source_span: source_spans[i]` to the i-th entry verbatim -- a two-element `[start_line, end_line]` array, matching `RecoveredNeed.source_span: Option<[u32; 2]>`. Skip the field entirely (do not set it to `null`) for any index whose `source_spans[i]` is `null`, or when `source_spans` is absent altogether -- the field's absence is what deserializes to `None` on the engine side, a JSON `null` would not.

This skill never touches a cluster's member needs. Member up-link RST edits are authored by `pharaoh-rev-cluster-synthesize` itself (`member_updates`) and persisted the same way any other skill-emitted `raw_rst` is -- outside this skill's Process entirely.

### Step 3: Wrap into `RecoveryResult`

```json
{
  "source_path": "<source_path>",
  "target_rst": "<target_rst>",
  "run": {"agent": "...", "model": "...", "prompt_hash": "...", "sources": ["..."]},
  "needs": [/* Step 2 array */]
}
```

This is the `reqs` -> `needs` adapter the engine's `record` verb expects.

### Step 4: Write the temp file

Write the `RecoveryResult` JSON to a temp file. Prefer `<workspace_dir>/rev-record-ledger-<run.agent-sanitized>.json` when a plan workspace is available, otherwise use a process-local temp file. The path must be stable for the duration of this single invocation only -- no cleanup contract beyond the invocation, the executor's workspace retention policy owns lifecycle.

### Step 5: Shell out to the CLI

Per `shared/data-access.md` Tier 1 discipline: first confirm `ubc --version` exits 0. Then, from `project_root`, run:

```
ubc agent reverse record --input <tempfile>
```

Capture stdout, stderr, and exit code. This command is a write, not one of the read commands `shared/data-access.md`'s Tier 1 table lists (`ubc build needs`, `ubc config`, `ubc check`, `ubc schema validate`, `ubc diff`) -- it follows the same Tier-1-first, run-from-project-root, parse-JSON-directly discipline that table establishes, and this skill is the only place in the skill tree permitted to invoke it (see `pharaoh-rev-cluster-synthesize` and `pharaoh-rev-atomicity-split`, both of which explicitly defer to this skill for the CLI call).

### Step 6: Return

On exit 0: parse stdout as JSON (FAIL if it does not parse) and return it verbatim as this skill's output. On non-zero exit: FAIL per Failure modes, naming stderr's first line. Do not retry, do not fabricate a success response.

## Failure modes

- `reqs` empty, or `source_path` / `target_rst` / `run` / `project_root` missing -> FAIL: `"pharaoh-rev-record-ledger: missing required input <name>"`.
- `ubc --version` non-zero exit (CLI unavailable) -> FAIL: `"ubc CLI not available. pharaoh-rev-record-ledger has no Tier 2/3 fallback for the write path -- ubCode MCP and raw file parsing are read-only per shared/data-access.md, and this skill's one CLI call is a write."`
- Temp file write failure -> FAIL: `"pharaoh-rev-record-ledger: could not write temp file <path>"`.
- `ubc agent reverse record` non-zero exit -> FAIL: `"ubc agent reverse record failed: <stderr first line>"`. No retry.
- CLI stdout does not parse as JSON despite exit 0 -> FAIL: `"ubc agent reverse record returned non-JSON stdout"`.

## Last step

After the CLI call returns, invoke `pharaoh-output-validate` on the raw stdout: `mode: "block"`, `target_schema: "json_obj"`, `output_text: <raw CLI stdout>`, `schema_context: {required_keys: [], allowed_unknown_keys: true}`. Attach the returned validation JSON to this skill's output under `review`. If `valid` is `false`, return a non-success status with the validation findings verbatim and do NOT report the ledger write as complete -- the caller inspects the CLI's stderr and re-invokes this skill once the underlying issue (a malformed `RecoveryResult`, or a CLI-side fault) is fixed. There is no dedicated `*-regenerate` skill for this step: the wrap in Steps 2-3 is deterministic, so a validation failure here points at the CLI response or this skill's own wrap, never at requirement content -- content quality was already reviewed upstream, at each rung's own emission Last step (`pharaoh-rev-cluster-synthesize` -> `pharaoh-feat-review`, `pharaoh-rev-atomicity-split` -> `pharaoh-req-review`, or the plan-level `review_*` / `grounding_*` tasks for `pharaoh-req-from-code`). This step checks only whether the persistence call itself succeeded and returned a well-shaped response -- structural, not prose-quality, the same distinction `pharaoh-req-codelink-annotate`'s Last step draws for its own one-line insert.

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

## Composition

The terminal write task of a reverse-recovery plan chain: `pharaoh-write-plan`'s `reverse-recover-rung` template dispatches one instance of this skill per file (extraction rung) or per cluster (synthesis rung), each `depends_on` that item's own emission AND its review / grounding tasks (`review_*` / `grounding_*` at an extraction rung, `review_cluster_synth_*` / `review_atomicity_split_*` at a synthesis rung) -- the ledger records only reviewed needs, never a raw unreviewed emission -- and, where applicable, its `pharaoh-req-codelink-annotate` task. This skill never fans out itself -- the plan's per-item unrolling is what produces N calls for N emissions. It never receives or applies a cluster's member up-links either -- `pharaoh-rev-cluster-synthesize` authors those directly as RST (`member_updates`), persisted by the plan the same way any other skill-emitted `raw_rst` is, upstream of and independent from this skill's ledger write. After this skill returns, the terminal `pharaoh-quality-gate` task depends on every `record_ledger_*` instance alongside the review and grounding tasks, so a plan cannot report success while a ledger write silently failed.

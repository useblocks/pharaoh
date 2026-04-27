---
name: pharaoh-status-lifecycle-check
description: Use when running a release-gate check over a full sphinx-needs corpus to confirm that zero needs remain in the initial `draft` status. Single mechanical binary gate — aggregates `status` across every need in `needs.json`, compares against the initial-state declaration in `workflows.yaml`, and returns pass/fail plus per-status counts. Advisory by default (pre-release development passes); release pipelines override `enforce=true` so any draft blocks the gate.
---

# pharaoh-status-lifecycle-check

## When to use

Invoke from a release pipeline, from `pharaoh-quality-gate` as the delegated check for the `status-lifecycle-healthy` invariant, or standalone when auditing whether a corpus is past the draft stage. Reads the project's `workflows.yaml` (for the initial-state name) plus `needs.json` (for each need's current `status`), buckets the needs, and emits a single findings JSON with `draft_count` and an `overall` verdict.

Do NOT invoke to check whether a single transition `from → to` is legal — that is the per-need state-machine question answered by `pharaoh-lifecycle-check`. That skill checks one need, one proposed transition, consults the `transitions` list with `requires:` prerequisites, and answers "is this move allowed right now?". This skill answers a different question over a different input: given the whole corpus, how many needs are still in the initial `draft` bucket, and does the release policy tolerate any? No per-need transition walk, no prerequisite resolution — only the binary "current status bucket" aggregation.

Do NOT invoke to score percentage thresholds like "≥50% past draft". The plan that commissioned this atom explicitly rejects fuzzy thresholds for release gates. Under `enforce=true` the gate is binary: zero drafts pass, one draft fails. Under `enforce=false` the output reports counts without failing, so callers still see the distribution.

Do NOT invoke to transition needs. Read-only audit.

## Atomicity

- (a) Indivisible: one `workflows.yaml` + one `needs.json` in → one findings JSON out. No per-need transition checks, no set-level re-authoring, no dispatch of other skills.
- (b) Input: `{workflow_path: <str>, needs_json_path: <str>, enforce: bool (default false)}`. Output: findings JSON per the shape in `## Output` below.
- (c) Reward: fixtures under `skills/pharaoh-status-lifecycle-check/fixtures/` — one per outcome branch:
  1. `all-draft-enforcing/` — every need `status: draft`, `enforce: true`. Expected: `overall: "fail"`, `draft_count` equals total, `blockers` lists the draft need ids.
  2. `all-draft-advisory/` — every need `status: draft`, `enforce: false`. Expected: `overall: "pass"` with an advisory `blockers` entry describing the drafts without failing the gate.
  3. `mixed-enforcing/` — some drafts, some past draft, `enforce: true`. Expected: `overall: "fail"`, `blockers` lists only the draft need ids.
  4. `fully-reviewed-enforcing/` — every need past draft, `enforce: true`. Expected: `overall: "pass"`, empty `blockers`.

  Pass = each fixture's actual output matches `expected-output.json` modulo ordering of need ids inside the `blockers` list.
- (d) Reusable across projects — lifecycle state names come from `workflows.yaml` (the project declares them); only the bucket named by `initial_state` (or the literal `draft` fallback) triggers the gate. No project-specific vocabulary in the base.
- (e) Read-only. Does not modify `workflows.yaml`, `needs.json`, or any need status.

## Input

- `workflow_path`: absolute path to the project's `workflows.yaml` (typically `.pharaoh/project/workflows.yaml`). The skill reads two keys:
  - `initial_state` (optional): the state name that signals "not yet reviewed". If absent, the skill falls back to the literal string `"draft"` and records a note.
  - `lifecycle_states` (optional): map of declared state names. Used only to validate that every observed status is declared; unknown statuses surface in `notes` but do not change the verdict.
- `needs_json_path`: absolute path to the project's `needs.json` (typically `docs/_build/needs/needs.json`). The skill reads the flat ID map and inspects each entry's `status` field.
- `enforce`: boolean, default `false`. When `false`, the skill runs in advisory mode — counts and lists drafts but always emits `overall: "pass"`. When `true`, any draft flips `overall` to `"fail"`.

Edge cases:
- `workflow_path` missing or unparseable → emit `overall: "fail"` with blocker `"workflows.yaml unresolved: <path>"` regardless of `enforce` (cannot decide without the initial-state name).
- `needs_json_path` missing or unparseable → emit `overall: "fail"` with blocker `"needs.json unresolved: <path>"` regardless of `enforce`.
- `needs.json` contains zero needs → emit `overall: "pass"`, `draft_count: 0`, `notes: ["needs.json empty — nothing to gate"]`.
- Need lacks a `status` field → bucket it under the literal key `"<missing>"`, count it as past-draft for gate purposes, and surface it in `notes`. This avoids crashing on malformed corpora while keeping the gate focused on `draft`.

## Output

```json
{
  "needs_by_status": {"draft": 40, "reviewed": 0, "approved": 0, "released": 0},
  "draft_count": 40,
  "enforce": true,
  "overall": "fail",
  "blockers": [
    "40 needs still in draft status; release gate requires zero drafts",
    "comp_req__example_a",
    "comp_req__example_b",
    "..."
  ],
  "notes": []
}
```

Fields:
- `needs_by_status`: bucket counts keyed by every status value observed in `needs.json`. Entries with zero are included for states declared in `workflows.yaml.lifecycle_states` so downstream dashboards see a stable shape; observed-but-undeclared statuses are included with their actual count and added to `notes`.
- `draft_count`: count of needs whose status equals the `initial_state` from `workflows.yaml` (fallback literal `"draft"`).
- `enforce`: echo of the input flag so downstream callers can distinguish advisory from release runs without re-reading their own config.
- `overall`: `"pass"` when `enforce=false` OR `draft_count == 0`. `"fail"` otherwise, or when preconditions (workflow/needs files) failed to resolve.
- `blockers`: in `enforce=true` mode with `draft_count > 0`, one summary line plus one entry per draft need id (capped at the first 500 ids to bound output size; overflow surfaces as a single `"... and N more"` line). In advisory mode with `draft_count > 0`, a single informational entry like `"advisory: 40 needs in draft; release gate not enforced"` — `overall` stays `"pass"`. In pass cases, empty list.
- `notes`: informational observations — fallback `initial_state` used, undeclared statuses observed, missing `status` fields, empty corpus.

## Detection rule

One mechanical check. No LLM judgement.

### 1. `draft_count_against_enforce`

**Check:** Parse `workflows.yaml` for `initial_state` (fallback `"draft"`). Iterate `needs.json`, count needs whose `status` equals the initial-state name. If `enforce=true` and the count is non-zero, fail. Otherwise pass.

**Detection:**
```bash
# Initial state name (fallback to literal "draft"):
initial=$(python -c "import yaml; d=yaml.safe_load(open('$workflow_path')); print(d.get('initial_state','draft'))")

# Count drafts:
python -c "
import json, sys
needs = json.load(open('$needs_json_path'))
items = needs if isinstance(needs, list) else needs.get('needs', needs)
if isinstance(items, dict):
    items = items.values()
count = sum(1 for n in items if n.get('status') == '$initial')
print(count)
"

# Gate:
# enforce == true AND count > 0  → fail
# else                           → pass
```

The skill performs the same extraction in whatever runtime the caller invokes (direct tool use, subagent shell); the pseudocode above is the reference implementation.

## Tailoring extension point

The `initial_state` name is read from `workflows.yaml` — the project tailors what "draft" means by declaring the state there. No other knobs are exposed on this skill; a project that wants percentage-based reporting should wire a separate metric collector rather than weaken this binary gate.

## Composition

Role: `atom-check`.

Called from `pharaoh-quality-gate` as the delegated check for the `status-lifecycle-healthy` invariant (pass requirement: `overall == "pass"` with `enforce=true` set by the release pipeline). Also callable standalone from any release workflow that wants the binary gate without the full quality-gate pipeline. Never dispatches other skills. Never modifies tailoring, needs.json, or need status.

Distinct from `pharaoh-lifecycle-check`: that skill is per-need and consults the `transitions` list (`from → to` legality with `requires:` prerequisites); this skill is corpus-wide and consults only the initial-state bucket.

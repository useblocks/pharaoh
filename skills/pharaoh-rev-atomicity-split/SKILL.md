---
name: pharaoh-rev-atomicity-split
description: Use when a recovered need bundles several atomic requirements and must be split into atomic needs without losing its links. Detects a conjunction or more than one `shall` inside a single recovered need's body, re-emits one atomic need per behavior, and carries the original need's up-links onto every atom unchanged. Leaves an already-atomic need untouched. Does NOT synthesize a new higher-rung need (that is `pharaoh-rev-cluster-synthesize`) and does NOT invoke the CLI (that is `pharaoh-rev-record-ledger`).
---

# pharaoh-rev-atomicity-split

## When to use

Invoke against one recovered need, either just emitted by `pharaoh-rev-cluster-synthesize` /
`pharaoh-req-from-code` or already written into the corpus and pulled back out of `needs.json`,
that a reviewer or an audit (`pharaoh-feat-review`, `pharaoh-req-review`, `pharaoh-process-audit`)
has flagged as over-consolidated: its body reads as more than one requirement bundled into one
need. This skill splits that one need into one atomic need per behavior and re-emits each atom
carrying the original's up-links, correcting the over-consolidation post-hoc.

Do NOT use to cluster lower needs or synthesize a missing upper rung -- that is
`pharaoh-rev-cluster-synthesize`. Do NOT use to write the split atoms to disk or invoke
`ubc agent reverse record` -- that is `pharaoh-rev-record-ledger`, the only skill allowed to
shell out to the CLI. Do NOT use on a need that is already atomic -- this skill detects that case
and leaves the need untouched rather than manufacturing a split. One invocation addresses one
recovered need. If an audit flags several over-consolidated needs, run this skill once per need.

## Tailoring awareness

The up-link field name each atom must carry comes from the consumer project's `ubproject.toml`
(`[[needs.extra_links]]`, e.g. a project-renamed `realizes` in place of `satisfies`) or
`.pharaoh/project/id-conventions.yaml` if present -- resolved the same way
`pharaoh-req-from-code` resolves the name it renders `parent_feat_ids` under. Do NOT hardcode
`satisfies` as the only possible up-link field name. The atomicity test itself (more than one
`shall`, or a coordinating conjunction joining modal-verb phrases within one shall clause) is the
same binary rule `pharaoh-req-review` applies on its `atomicity` axis. A project may extend it via
`checklists/requirement.md`, but the built-in rule is the default when no tailoring overrides it.

## Atomicity

- (a) Indivisible -- one recovered need in -> one or more atomic needs out. No clustering, no
  synthesis of a new higher-rung need, no CLI invocation, no file write. If the need is already
  atomic, the single unchanged need is the entire output -- no fan-out.
- (b) Input: `{recovered_need, project_root, tailoring_path?, reporter_id, on_missing_config?}`.
  Output: single JSON object `{"reqs": [{"id", "title", "type", "body", "satisfies", "status",
  "split_from", "raw_rst"}, ...]}`.
- (c) Reward: fixture `fixtures/basic/input-need.json` -- one `comp_req` need whose body bundles
  two `shall` statements and carries one up-link to a parent `feat`. Skill run against it produces
  output byte-exact matching `fixtures/basic/expected-output.json`: exactly two atoms, each with
  exactly one `shall` in its body, each carrying `satisfies: ["FEAT_csv_export"]` unchanged from
  the original, each `split_from` equal to the original need's id, and neither atom carrying a
  link to the other atom or back to the pre-split need id.
- (d) Reusable as the standard post-hoc fix for any over-consolidated need an audit or review
  skill flags, not limited to the reverse-recovery pipeline.
- (e) Composable -- strictly one phase (detect + split + re-emit). Never invokes
  `pharaoh-rev-cluster-synthesize`, never invokes `pharaoh-rev-record-ledger`, never calls the CLI
  itself.

## Input

- `recovered_need`: EITHER a need object with the shape below, OR a bare need-id string. When a
  bare string, resolve the object via `ubc build needs --format json` per
  `shared/data-access.md` Tier 1 (fall through to Tier 2 / Tier 3 per the same document if `ubc`
  is unavailable). FAIL per Failure modes if the id does not resolve.

  Need object shape:
  ```json
  {
    "id": "<need_id>",
    "type": "<directive>",
    "title": "<title>",
    "body": "<one or more shall clauses>",
    "status": "draft",
    "satisfies": ["<parent_1>", "..."]
  }
  ```
  `satisfies` is a stand-in name -- use the field name Tailoring awareness resolves for this
  project. Additional tailoring-declared fields present on the input (`source_doc`,
  `verification`, and similar) are carried through unchanged. This skill neither adds nor drops
  them.
- `project_root`: absolute path to the consumer project's root, used to resolve the up-link field
  name from `ubproject.toml`.
- `tailoring_path` (optional): absolute path to `.pharaoh/project/` for the atomicity checklist
  override and up-link field rename.
- `reporter_id`: short identifier for this agent, passed to review invocations at Last step.
- `on_missing_config` (optional): `"fail" | "prompt" | "use_default"`. Default `"prompt"`. Same
  semantics as `pharaoh-feat-draft-from-docs` Step 3, applied to up-link field resolution.

## Output

A single JSON object with one top-level key, `reqs`: the atomic needs replacing the input need
(two or more entries), or the input need alone, unchanged, when it was already atomic. Shape:

```json
{
  "reqs": [
    {
      "id": "<original_id>_01",
      "title": "<short_title_for_this_atom>",
      "type": "<original_type>",
      "body": "<single shall clause>",
      "satisfies": ["<parent_1>", "..."],
      "status": "<original_status>",
      "split_from": "<original_id>",
      "raw_rst": ".. <type>:: <short_title>\n   :id: ...\n   :status: ...\n   :satisfies: ...\n\n   <body>\n"
    }
  ]
}
```

Field semantics:

- `id` -- `<original_id>_<NN>`, zero-padded two-digit sequence starting at `01`, in the order the
  behaviors appear in the original body. The original id is never reused as an atom id -- it is
  retired in favor of its atoms.
- `type` -- equals the original need's `type`. Splitting changes cardinality, never rung.
- `satisfies` (or the tailored up-link field name) -- copied verbatim from the original need onto
  every atom. Never inverted, never pointed at a sibling atom, never pointed at the retired
  original id. See "Link direction" below.
- `status`, and any other tailoring-declared field present on the input (`source_doc`,
  `verification`) -- copied verbatim onto every atom.
- `split_from` -- the original need's id, present on every atom so the caller can identify which
  needs an atom replaces. Omitted when the need was already atomic and the sole output item is the
  unchanged original (nothing was split from anything).
- `raw_rst` -- the directive block for that atom alone, in the same format
  `pharaoh-req-from-code` renders. Carries the tailored up-link field pointing at the original's
  parents, never at another atom.

The output is one JSON object -- no surrounding prose, no concatenated RST outside the JSON.

### Link direction

Sphinx-needs convention: a need cites its parent via an up-link (child cites parent). The
original need's up-links point at its own parent, one rung above. Splitting a need changes how
many atomic needs exist at that rung, not what they trace to -- every atom inherits the exact same
up-link set the original carried. Do NOT invert direction (an atom must never gain a down-link),
and do NOT link the atoms to each other or to the retired original id -- they are independent
siblings, not a new mini-hierarchy.

## Output schema

Validated as `json_obj` by `pharaoh-output-validate`. Validator checks:

1. Top-level is a JSON object with exactly one required key, `reqs` (a non-empty list).
2. Every `reqs[*]` item has the keys `id`, `title`, `type`, `body`, `satisfies` (or the resolved
   tailored up-link field name), `status`, `raw_rst`. `split_from` is present on every item when
   `len(reqs) > 1`, and absent when `len(reqs) == 1` and that item is byte-identical to the input
   need (the already-atomic case).
3. Every `reqs[*].type` equals the input need's `type`.
4. Every `reqs[*]` up-link field value equals the input need's up-link field value (same list,
   same order).
5. No `reqs[*]` up-link field value contains another `reqs[*].id` or the original need's id --
   atoms never link to each other or to the retired original.
6. Each `reqs[*].body` contains exactly one `shall` and no coordinating conjunction (`, and`/
   ` and `/`, or`/` or `) joining modal-verb phrases within that clause -- the atomicity binary
   axis from `pharaoh-req-review` must pass on every emitted atom.
7. `raw_rst` matches the RST directive Stage 1 + Stage 2 regex from `pharaoh-req-from-code`
   `## Output schema`, with directive name = `type` and `:id:` / `:status:` present.
8. When `len(reqs) > 1`: `reqs[*].id` values are exactly `<split_from>_01`, `<split_from>_02`, ...
   with no gaps and no repeats.

## Process

### Step 1: Resolve tailoring

Read `<project_root>/ubproject.toml` and, if present, `<tailoring_path>/id-conventions.yaml`.
Resolve the up-link field name the same way `pharaoh-req-from-code` resolves the name it renders
`parent_feat_ids` under (declared rename in `ubproject.toml` -> use it, else `satisfies`). Resolve
the atomicity rule from `<tailoring_path>/checklists/requirement.md` if it overrides the default,
otherwise use the built-in rule (more than one `shall`, or a coordinating conjunction joining
modal-verb phrases within one shall clause).

If `project_root` has no `ubproject.toml` and no tailored up-link rename is discoverable, branch
on `on_missing_config`. `"fail"` -> FAIL. `"prompt"` -> return
`{status: "needs_confirmation", proposal: {up_link_field: "satisfies"}}` without emitting.
`"use_default"` -> proceed with `satisfies`.

### Step 2: Load the recovered need

If `recovered_need` is an object, use it directly. If it is a bare id string, resolve it via
`ubc build needs --format json` per `shared/data-access.md` Tier 1, falling through to Tier 2
then Tier 3 if `ubc` is unavailable. FAIL per Failure modes if no tier resolves the id.

### Step 3: Detect atomicity violation

Apply the resolved atomicity rule (Step 1) to the need's `body`:

- Count `shall` occurrences. More than one -> bundled.
- Within each shall clause, check for `, and`/` and `/`, or`/` or ` joining two verb phrases both
  governed by the same `shall` -- e.g. "shall detect X and activate Y" -- -> bundled.

If neither condition holds, the need is already atomic. Go to Step 6 (untouched case).

If either condition holds, go to Step 4.

### Step 4: Segment into atomic behaviors

Walk the body in original order and extract one atomic behavior statement per distinct action:

- One statement per sentence already containing its own `shall`.
- Within a single shall clause joined by a coordinating conjunction, split at the conjunction --
  each resulting fragment keeps the shared subject and becomes its own `shall` statement (e.g.
  "The X shall detect A and activate B" -> "The X shall detect A." / "The X shall activate B.").

Discard no content: every clause in the original body must appear in exactly one atom. If a
fragment is not independently meaningful without the other (a genuine sub-step of a single
action, not a second behavior), it is not a split candidate -- leave it fused and note this is a
borderline case in a trailing `[FLAG]` rather than manufacturing a false split.

### Step 5: Re-emit each atom

For each segmented behavior, in original order, starting at `01`:

- `id`: `<original_id>_<NN>`.
- `title`: 3-6 word summary of that atom's action, derived from its subject + primary verb.
- `type`: the original need's `type`, unchanged.
- `body`: the single shall statement for that atom.
- The resolved up-link field (Step 1): the original need's full value, copied verbatim.
- `status`: the original need's `status`, copied verbatim.
- Any other tailoring-declared field present on the original (`source_doc`, `verification`):
  copied verbatim.
- `split_from`: the original need's id.
- `raw_rst`: rendered in the same directive-block format as `pharaoh-req-from-code` Step 5a.

### Step 5a: Self-check

Re-apply the Step 3 atomicity rule to every emitted atom's body. Each must now pass (exactly one
`shall`, no conjunction). If an atom still fails, attempt one further re-split of that atom only.
If it still fails after two total attempts, emit it anyway with a trailing note:

```
[DIAGNOSTIC] atom "<id>" still not atomic after 2 split attempts.
Manual correction required before re-running pharaoh-req-review.
```

Do not loop past two attempts.

### Step 6: Already-atomic case

If Step 3 found no bundling, emit `reqs` as a single-element list containing the original need
unchanged (same `id`, `title`, `type`, `body`, up-link value, `status`) with no `split_from` field.
No re-split, no id suffix, no atom fabricated.

### Step 7: Return

Emit the single JSON object `{"reqs": [...]}` per the Output shape. Nothing else on stdout -- no
prose wrapper, no fenced code block.

## Failure modes

- `recovered_need` is a bare id string that no tier resolves -> FAIL: "recovered need <id> did not
  resolve via any data-access tier."
- `recovered_need.body` contains zero `shall` clauses -> FAIL: "recovered need <id> has no shall
  clause -- not a valid requirement to split."
- Up-link field unresolved and `on_missing_config == "fail"` -> FAIL per Step 1.
- Segmentation (Step 4) would discard body content rather than reassign it to an atom -> FAIL
  rather than emit an atom that silently drops a constraint the original stated.

## Last step

After emitting the artefact, invoke `pharaoh-req-review` once per item in `reqs`, passing that
item's `raw_rst` as `target`. Attach the returned review JSON to the skill's output under
`review`, keyed by atom `id`. If any atom's review emits an axis with `score: 0` or
`severity: critical`, return a non-success status with that atom's review findings verbatim and do
NOT finalize the split -- the caller re-invokes `pharaoh-req-regenerate` for that specific atom
using the attached findings, then re-attaches the regenerated atom in place of the failing one.

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and
enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check`
in `pharaoh-quality-gate`.

## Composition

Invoked post-hoc whenever `pharaoh-req-review`, `pharaoh-feat-review`, or `pharaoh-process-audit`
flags a recovered need as bundling more than one behavior -- including the case
`pharaoh-rev-cluster-synthesize`'s Failure modes describes, where a synthesized higher need turns
out over-broad. After this skill emits `reqs`, `pharaoh-rev-record-ledger` wraps the atoms into
the engine's `RecoveryResult` shape (`reqs` -> `needs`) and runs
`ubc agent reverse record --input <tempfile>` -- the only legal way a plan-DAG task reaches the
CLI. That call writes only the advisory ledger for the atoms (`record` never edits RST or links).
Each atom's up-link field is already correct as emitted by this skill (Step 5, copied verbatim
from the retired original), so no further RST authoring is needed for it downstream. This skill
never invokes the CLI, never clusters, never synthesizes, and never emits a down-link from an atom
to another atom or to the retired original.

---
name: pharaoh-rev-cluster-synthesize
description: Use when synthesizing one higher-level need from a cluster of lower needs plus the diffuse intent signal in the git surface, authoring the up-link RST edit each cluster member needs to cite the new need. Does NOT cluster lower needs itself, does NOT split an over-consolidated result (that is `pharaoh-rev-atomicity-split`), and does NOT invoke the CLI or write the ledger (that is `pharaoh-rev-record-ledger`, which never touches RST).
---

# pharaoh-rev-cluster-synthesize

## When to use

Invoke when reverse-engineering a requirements model from an existing project where a cluster of lower-rung needs (e.g. component requirements) already exists but has no upper-rung anchor (e.g. no feature that groups them). The caller has already computed the cluster -- grouping is a separate upstream step, not this skill's job -- and has gathered diffuse intent signal from the git surface (commit messages, PR titles and descriptions, changelog entries) via `forge::fetch_intent` or an equivalent selection step. This skill reads the cluster's member bodies, reads the intent snippets, and synthesizes exactly one higher-rung need that is grounded in both.

Do NOT use to cluster lower needs -- clustering is a precomputed upstream step. A plan-DAG `foreach` task dispatches one call of this skill per cluster. Do NOT use to fix an over-consolidated synthesis result -- that is `pharaoh-rev-atomicity-split`. Do NOT use to invoke `ubc agent reverse record` or write the advisory ledger -- that is `pharaoh-rev-record-ledger`, the only skill allowed to shell out to the CLI, and it never edits RST. This skill DOES author RST: both the synthesized need's own `raw_rst` and, in `member_updates`, the up-link edit each cluster member's own directive needs -- skills author RST in this family, the engine's `record` verb never does.

## Tailoring awareness

The emitted directive name and ID prefix come from the consumer project's `ubproject.toml` `[[needs.types]]` (or `.pharaoh/project/id-conventions.yaml` if present). The caller passes `target_level` (default `feat`) -- use it verbatim as the directive name. Do NOT hardcode `feat` as the only acceptable type. A project may call its upper rung `story`, `capability`, or `epic`.

## Atomicity

- (a) Indivisible -- one invocation reads one precomputed cluster (member ids) plus its intent snippets and emits exactly one synthesized need, plus that need's up-link edit for each cluster member. No clustering. No fan-out across clusters (the caller's `foreach` handles that). No CLI invocation, no ledger write -- authoring RST (the synthesized need and its members' up-link edits) is this skill's own output, persisted by the plan the normal way any skill's `raw_rst` output is persisted, not something `ubc agent reverse record` does.
- (b) Input: `{cluster_id, members: list[str], intent_snippets: list[{id, source, text}], target_level, project_root, tailoring_path?, papyrus_workspace?, reporter_id, on_missing_config?}`. Output: single JSON object `{"reqs": [{"id", "title", "type", "body", "intent_refs", "intent_gap", "cluster_id", "raw_rst"}], "member_updates": [{"member_id", "file", "line", "link_field", "raw_rst"}, ...]}`.
- (c) Reward: deterministic fixture -- a cluster of 3 lower reqs sharing one theme plus 2 intent snippets that name that theme explicitly. Scorer checks: (1) exactly one emitted need, (2) the emitted need's `raw_rst` carries no down-link to the members, (3) `member_updates` lists all 3 member ids, each entry's `raw_rst` carrying the resolved `link_field` extended to include the emitted need's `id` and every other pre-existing field on that member unchanged, (4) `intent_refs` cites at least one of the 2 snippet ids, (5) `intent_gap` is `false`, (6) the emitted `type` equals `target_level`, (7) the body's vocabulary overlaps with both the members' shared theme and the intent snippets (substring match, case-insensitive), (8) both the emitted need's `raw_rst` and every `member_updates[*].raw_rst` match the directive Stage 1 + Stage 2 regex from `pharaoh-req-from-code` `## Output schema`.
- (d) Reusable across any bottom-up reverse-engineering workflow synthesizing a missing upper rung from an existing lower-rung corpus plus repository history.
- (e) Composable -- strictly one phase (cluster + intent -> one synthesized need plus its members' up-link edits). Never invokes clustering, `pharaoh-rev-atomicity-split`, or `pharaoh-rev-record-ledger` itself, and never shells out to the CLI or writes the ledger. A plan emitted by `pharaoh-write-plan` composes this skill (one call per cluster) with `pharaoh-rev-atomicity-split` and `pharaoh-rev-record-ledger` downstream.

## Input

- `cluster_id`: short identifier for the precomputed cluster, used to build the synthesized need's id slug and carried through to the output for traceability.
- `members`: list of lower-need ids in the cluster (at least 2). The skill resolves each member's full existing need object (`id`, `type`, `title`, `body`/content, `status`, existing links including the current `link_field` value, `file`, `line`) via `ubc build needs --format json` per `shared/data-access.md` Tier 1 (fall through to Tier 2 / Tier 3 per the same document if `ubc` is unavailable) -- full resolution, not just the body, because Step 6 re-renders each member's whole directive with its up-link field extended. The caller passes ids only, never pre-resolved bodies.
- `intent_snippets`: list of `{id, source, text}` objects, already gathered by the caller (e.g. `forge::fetch_intent` or manually selected commit/PR text). `source` is a short provenance label (`"commit a1b2c3d"`, `"PR #142 description"`). May be empty -- see intent-gap handling in Process.
- `target_level`: directive name for the synthesized need. Must match a `[[needs.types]].directive` in the consumer project's `ubproject.toml`. Default `feat`. The emitted directive uses this name verbatim.
- `project_root`: absolute path to the consumer project's root, used to resolve the ID prefix from `ubproject.toml`. If undeclared, fall back to `<target_level>__`.
- `tailoring_path` (optional): absolute path to `.pharaoh/project/` for extra-field declarations (e.g. whether a project-specific up-link name replaces `satisfies` for the members' link to `target_level`).
- `papyrus_workspace` (optional): path to `.papyrus/` for canonical-term coordination with concurrent agents. Absent -> no-memory mode.
- `reporter_id`: short identifier for this agent, passed to `pharaoh-decision-record` calls.
- `on_missing_config` (optional): `"fail" | "prompt" | "use_default"`. Default `"prompt"`. Same semantics as `pharaoh-feat-draft-from-docs` Step 3.

## Output

A single JSON object with two top-level keys: `reqs` (a one-element list -- one synthesized need per invocation) and `member_updates` (one RST edit per cluster member, adding the up-link that member must carry to the new need). Shape:

```json
{
  "reqs": [
    {
      "id": "<id_prefix><snake_case_id>",
      "title": "<short_title>",
      "type": "<target_level>",
      "body": "<synthesized higher-rung capability statement, grounded in the cluster and, where available, the intent signal>",
      "intent_refs": ["<intent_snippet_id>", "..."],
      "intent_gap": false,
      "cluster_id": "<cluster_id>",
      "raw_rst": ".. <target_level>:: <short_title>\n   :id: ...\n   :status: draft\n\n   <body>\n"
    }
  ],
  "member_updates": [
    {
      "member_id": "<member_1>",
      "file": "<path resolved via Tier 1>",
      "line": <line_no_resolved_via_tier_1>,
      "link_field": "<up_link_field_name>",
      "raw_rst": ".. <member_type>:: <member_title>\n   :id: <member_1>\n   :status: <member_status>\n   ...\n   :<link_field>: ..., <reqs[0].id>\n\n   <member_body>\n"
    }
  ]
}
```

Field semantics:

- `id` -- `<id_prefix><snake_case_id>` resolved the same way as `pharaoh-feat-draft-from-docs` Step 3 (declared `prefix` -> use it verbatim, declared type with no prefix -> `<target_level>__`). `<snake_case_id>` is derived from the synthesized title.
- `type` -- equals input `target_level`.
- `intent_refs` -- the subset of `intent_snippets[*].id` that actually grounded the synthesized body. Empty list when no snippet contributed.
- `intent_gap` -- `true` when no `intent_snippets` entry shares vocabulary or theme with the cluster, `false` otherwise. See Process Step 4.
- `cluster_id` -- echoes the input, letting the caller reconcile output against the precomputed cluster list.
- `raw_rst` -- exactly the directive block as it would appear pasted into an RST file, for the synthesized need alone. It carries no `:satisfies:` (or any other down-pointing link) to the cluster -- a higher need never authors a link down to the needs it summarizes, it only ever appears as the target of their up-links. Downstream skills that need the directive text read it from here.
- `member_updates` -- one entry per cluster member, sphinx-needs convention (child cites parent): this skill authors the RST edit itself, it does not merely describe one for another skill to apply. `link_field` is the rung's configured up-link name for `target_level` (`satisfies` unless `ubproject.toml` or `tailoring_path` declares a rename), resolved the same way `pharaoh-req-from-code` resolves the name it renders `parent_feat_ids` under, and is the same value on every entry. `file` / `line` are the member's existing directive location, resolved via Tier 1, letting the caller splice the updated block back in place rather than append a duplicate. `raw_rst` is the member's own directive block, re-rendered with every pre-existing field unchanged except `link_field`, whose value is extended by `reqs[0].id` (deduplicated, existing order preserved, appended if new). This is a plan-persisted RST edit like any other skill output -- `pharaoh-rev-record-ledger` never sees `member_updates` and never touches RST. It is not part of the engine's `RecoveryResult` shape.

The output is one JSON object -- no surrounding prose, no concatenated RST outside the JSON.

## Output schema

Validated as `json_obj` by `pharaoh-output-validate`. Validator checks:

1. Top-level is a JSON object with exactly two required keys: `reqs` (a list of exactly one item) and `member_updates` (a non-empty list).
2. The `reqs` item has the keys `id`, `title`, `type`, `body`, `intent_refs`, `intent_gap`, `cluster_id`, `raw_rst`, and does NOT have a `satisfies` key or any other down-link key.
3. `type` equals input `target_level`.
4. `member_updates[*].member_id` values equal the input `members` list (same set, order-independent). Every entry has `file`, `line`, `link_field` (non-empty string, the same value on every entry), and `raw_rst`.
5. `intent_gap` is a boolean. `intent_refs` is `[]` whenever `intent_gap` is `true`.
6. `raw_rst` (on the `reqs` item) matches the RST directive Stage 1 + Stage 2 regex from `pharaoh-req-from-code` `## Output schema`, with directive name = `type` and `:id:` / `:status:` present, and contains no `:satisfies:` (or configured down-link) field.
7. Every `member_updates[*].raw_rst` also matches that Stage 1 + Stage 2 regex, with directive name = that member's own resolved `type`, and its `:<link_field>:` option value contains `reqs[0].id`.
8. `id` (on the `reqs` item) matches the resolved `<id_prefix><snake_case_id>` pattern.

## Process

### Step 1: Resolve tailoring

Read `<project_root>/ubproject.toml`. Find the `[[needs.types]]` entry whose `directive` equals `target_level`. Resolve the id prefix the same way as `pharaoh-feat-draft-from-docs` Step 3:

1. Declared type with a `prefix` field -> use it verbatim.
2. Declared type without a `prefix` -> use `<target_level>__` silently.
3. Type NOT declared (or `ubproject.toml` missing) -> branch on `on_missing_config` exactly as that skill does, returning `{status: "needs_confirmation", proposal: ...}` on `"prompt"` and returning without emitting.

### Step 2: Resolve member need objects (Tier 1)

For each id in `members`, resolve its full existing need object -- `type`, `title`, `body`/content, `status`, current links (including whatever it already carries under the up-link field resolved in Step 1), `file`, and `line` -- via `ubc build needs --format json` (`shared/data-access.md` Tier 1). Fall through to Tier 2 (ubCode MCP) then Tier 3 (raw file parsing) per the same document if `ubc` is unavailable. A `members` entry that cannot be resolved by any tier is dropped with a logged warning. If fewer than 2 members remain resolvable, FAIL per Failure modes. Full resolution (not just body) is required because Step 6 re-renders each member's whole directive with its up-link field extended -- dropping any pre-existing field would silently lose it.

### Step 3: Query Papyrus for canonical names (if workspace provided)

Only if `papyrus_workspace` is provided. Query `pharaoh-context-gather` with `mode="semantic"` for the shared concept the cluster expresses, before naming it in the synthesized title or body. Reuse a returned canonical name verbatim. Skip this step in no-memory mode.

### Step 4: Grounded synthesis -- never abstract in a vacuum

Identify the single theme shared across all resolved member bodies: what capability, taken together, do they compose? This shared theme is the mandatory grounding source. Every synthesized need traces back to it.

Then check the intent snippets against that theme:

1. For each entry in `intent_snippets`, test whether its `text` names the same theme (shared vocabulary, not merely topical proximity).
2. Snippets that pass become `intent_refs`. Use their language to sharpen the synthesized title and body -- prefer the product-facing term a commit message or PR description uses over an internal term implied only by the members.
3. If zero snippets pass (including when `intent_snippets` is empty), set `intent_gap: true` and `intent_refs: []`. Synthesize from the member theme alone. Do not hold back emission for lack of intent signal, and do not invent a plausible-sounding commit or PR reference to fill the gap. An intent-gap marks the synthesis as ungrounded-by-intent for a human or `pharaoh-feat-review` to weigh, not a reason to fabricate one.

Never fabricate: the synthesized body may state only what the combined member bodies and, when present, the qualifying intent snippets actually support. A synthesized need that adds a capability, constraint, or scope absent from both sources is a fabrication and MUST NOT be emitted -- narrow the body instead.

### Step 5: Record newly surfaced concepts in Papyrus

Only if `papyrus_workspace` is provided. If the synthesized title or body introduces a canonical name Step 3 did not return, invoke `pharaoh-decision-record` with `type: "fact"`, the chosen `canonical_name`, a one-sentence `body`, `reporter_id`, and `tags: ["origin:rev-cluster-synthesize", "cluster:<cluster_id>"]`. On `"duplicate"`, re-query and adopt the existing spelling.

### Step 6: Emit

Build the single `reqs[0]` entry per the Output shape: `id`, `title`, `type` (= `target_level`), `body`, `intent_refs`, `intent_gap`, `cluster_id`, `raw_rst` (no `:satisfies:` or any other down-link to the members).

Then build `member_updates`, one entry per resolved member (the `link_field` name is resolved the same way `pharaoh-req-from-code` resolves the name it renders `parent_feat_ids` under -- declared rename in `ubproject.toml` / `tailoring_path`, else `satisfies` -- and is the same value on every entry):

1. Read the member's current `link_field` value from its Step 2 resolution (empty list if the field is absent).
2. Extend it with `reqs[0].id`, deduplicated, existing order preserved, appended if new.
3. Re-render the member's full directive block as `raw_rst`, in the same format `pharaoh-req-from-code` renders, with every pre-existing field (`id`, `type`, `title`, `status`, other links, content) unchanged except the extended `link_field` value. Carrying every pre-existing field forward, not a bare option-line patch, is deliberate -- the plan persists this `raw_rst` as the member's new directive text in place, so nothing the member already had is put at risk of being dropped.
4. Emit `{member_id, file, line, link_field, raw_rst}`, with `file` / `line` taken from the member's Step 2 resolution.

Nothing else on stdout -- no prose wrapper, no fenced code block.

## No-memory mode

If `papyrus_workspace` is absent, skip Steps 3 and 5. Proceed directly to 1, 2, 4, 6.

## Failure modes

- `members` has fewer than 2 resolvable ids after Step 2 -> FAIL: "cluster <cluster_id> has fewer than 2 resolvable members, synthesis requires a real cluster, not a single need."
- `ubproject.toml` missing or `target_level` undeclared with `on_missing_config="fail"` -> FAIL per Step 1.
- Over-consolidation: the resolved members do not share one coherent theme (Step 4 cannot identify a single grounding theme without discarding more than half the members). This skill does not refuse on incoherence -- it is not the atomicity gate. Emit the best-supported synthesis over the members that do share the identified theme. `pharaoh-feat-review` (invoked at Last step) and, if it flags the result, `pharaoh-rev-atomicity-split` downstream are the mechanism that catches and fixes an over-broad or incoherent result.
- Fabricated intent: an `intent_refs` entry whose snippet text does not actually name the synthesized theme is a defect in this skill's own output, not a valid result. Self-check before emitting: re-read every cited snippet and confirm it names the theme. Drop any that do not and re-evaluate `intent_gap` accordingly.
- `pharaoh-context-gather` / `pharaoh-decision-record` errors -> log and proceed as if no match found (never abort on memory-layer issues).

## Last step

After emitting the artefact, invoke `pharaoh-feat-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact -- the caller must regenerate by re-invoking this skill with the findings as input (there is no separate `*-regenerate` skill for this family).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

## Composition

A plan emitted by `pharaoh-write-plan` dispatches one instance of this skill per precomputed cluster via a `foreach` task. This skill's own output already carries the member up-link RST edits (`member_updates`). The plan persists them the same way it persists any other skill's `raw_rst` output, upstream of and independent from the ledger write. Downstream, `pharaoh-rev-atomicity-split` may re-split the synthesized need (`reqs[0]`) if `pharaoh-feat-review` (or a human auditor) finds it over-consolidated -- v1 of the `reverse-recover-rung` template does not re-point `member_updates` at the post-split atom ids when that happens (see that template's note next to `atomicity_split_*`). `pharaoh-rev-record-ledger` then wraps the resulting `reqs` alone (`reqs` -> `needs`) into the engine's `RecoveryResult` shape and runs `ubc agent reverse record --input <tempfile>` -- the only legal way a plan-DAG task reaches the CLI, and a ledger-only write that never touches `member_updates` or any RST. This skill never invokes the CLI, never clusters, never splits, and never authors a down-link from the synthesized need to its members.

---
name: pharaoh-feat-review
description: Use when auditing a single feature-level need (feat) against the generic feat review axes in `shared/checklists/feat.md` plus any per-project addenda in `.pharaoh/project/checklists/feat.md`. Emits structured findings JSON — per-axis pass/fail for mechanized axes, 0-3 score for subjective axes. Mirrors `pharaoh-req-review`'s shape for feat-level artefacts.
chains_from: [pharaoh-feat-draft-from-docs]
chains_to: []
---

# pharaoh-feat-review

## When to use

Invoke after `pharaoh-feat-draft-from-docs` emitted a feat, or on an existing feat need-id in needs.json. Part of the self-review invariant — see [`shared/self-review-invariant.md`](../shared/self-review-invariant.md).

Do NOT review comp_reqs or architecture — use `pharaoh-req-review` or `pharaoh-arch-review`. Do NOT re-author — invoke `pharaoh-feat-draft-from-docs` again with the review findings as input if regeneration is needed.

## Atomicity

- (a) One feat + one checklist in → one findings JSON out.
- (b) Input: `{target: <feat_directive_rst_or_need_id>, checklist_path: <path>, tailoring_path: <path>}`. Output: findings JSON with per-axis entries.
- (c) Reward: fixtures mirror `pharaoh-req-review` — one `passing.rst` and one `failing.rst` feat with expected findings JSON.
- (d) Reusable by any flow emitting feats.
- (e) Read-only.

## Input

- `target`: RST directive block for a feat, OR a `need_id` with `type: feat` present in needs.json.
- `checklist_path`: absolute path to `shared/checklists/feat.md`. Per-project extensions in `.pharaoh/project/checklists/feat.md` are appended if present.
- `tailoring_path`: absolute path to `.pharaoh/project/` root. Reads `artefact-catalog.yaml` for required/optional fields per the feat artefact type.

## Output

```json
{
  "need_id": "FEAT_example",
  "type": "feat",
  "axes": {
    "trace_to_parent_or_workflow":   {"passed": true, "reason": "links to wf__onboarding via :satisfies:"},
    "single_user_capability":        {"score": 3, "reason": "scope is one feature"},
    "source_doc_present_and_valid":  {"passed": true, "reason": "source_doc=docs/source/features/x.rst exists"},
    "required_fields_complete":      {"passed": true, "reason": "id, status, source_doc present"},
    "shall_clause_user_observable":  {"score": 2, "reason": "minor: names internal module"},
    "body_length_within_bounds":     {"passed": true, "reason": "body=8 lines, limit=15"},
    "no_comp_level_mechanism_leak":  {"score": 3, "reason": "no class / method names in body"},
    "naming_clarity":                {"score": 3, "reason": "FEAT_reqif_export — clear"}
  },
  "overall": "pass",
  "actions": []
}
```

## Review axes

See [`shared/checklists/feat.md`](../shared/checklists/feat.md) for the canonical axis list and rubric. Per-project extensions (e.g. Score's ASIL-level guidance, connector-family consistency (project-specific example)) are appended from `.pharaoh/project/checklists/feat.md` if present, with their own axis keys namespaced under `tailoring.*`.

## Composition

Invoked by `pharaoh-write-plan`-generated plans after every `pharaoh-feat-draft-from-docs` task. Also invoked ad-hoc per the self-review invariant. Coverage enforced by `pharaoh-self-review-coverage-check`.

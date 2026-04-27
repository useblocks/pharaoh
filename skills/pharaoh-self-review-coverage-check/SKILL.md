---
name: pharaoh-self-review-coverage-check
description: Use when verifying that every artefact emitted during a plan run received a matching review. For every drafted artefact in `runs/`, confirms a matching `<id>_review.json` exists and is non-empty. Closes the "draft emitted but review was skipped" failure class.
---

# pharaoh-self-review-coverage-check

## When to use

Invoke from `pharaoh-quality-gate.required_checks` on any plan that emitted drafts (reqs, feats, archs, vplans, fmeas, decisions, diagrams). Uses the draft↔review mapping in `shared/self-review-map.yaml` to determine which review skill was supposed to be invoked.

Do NOT use to re-invoke missing reviews — this skill only observes. Remediation is up to the plan's `on_fail` policy.

## Atomicity

- (a) Indivisible: one runs directory + one self-review map in → pass/fail + uncovered list out.
- (b) Input: `{runs_path: str, self_review_map_path: str}`. Output: JSON `{passed: bool, uncovered: list[{artefact_id, draft_skill, expected_review_skill}]}`.
- (c) Reward: fixtures in `pharaoh/skills/pharaoh-self-review-coverage-check/fixtures/`:
  1. `fully-covered/`: 2 `*_draft` return.json files + 2 matching `*_review.json` → `expected-fully-covered-pass.json` (`passed: true, uncovered: []`).
  2. `missing-review/`: 2 draft files + only 1 review file → `expected-missing-review-fail.json` (`passed: false`, `uncovered` names the missing pair).
  3. Empty review file (`{}`) counts as missing → failure with `reason: "review JSON is empty"`.
  4. Idempotent.
  5. `scalar-mapped/`: emission skill maps to a single scalar review skill; that review is invoked in the emission's `## Last step`. Expected: pass (backward-compatibility check — scalar mappings still work).
  6. `list-mapped-complete/`: emission skill maps to a list `[A, B]`; both A and B are invoked in the emission's `## Last step`. Expected: pass.
  7. `list-mapped-partial/`: emission skill maps to a list `[A, B]`; only A is invoked. Expected: fail with `uncovered` naming B as the missing `expected_review_skill`.
  
  Pass = all 7.
- (d) Reusable by any plan.
- (e) Read-only.

## Input

- `runs_path`: absolute path to runs directory. Must contain `*_draft.json` files (draft outputs) and `*_review.json` files (review outputs). Files may be under per-task subdirectories.
- `self_review_map_path`: absolute path to `shared/self-review-map.yaml`. Maps each draft skill to its review skill.

## Output

```json
{
  "passed": false,
  "uncovered": [
    {
      "artefact_id": "REQ_example_02",
      "draft_skill": "pharaoh-req-draft",
      "expected_review_skill": "pharaoh-req-review",
      "reason": "no matching *_review.json found"
    }
  ]
}
```

## Detection rule

For every `<run_dir>/**/<id>_draft.json` OR every entry in `<run_dir>/**/return.json` with `emitted: [...]`:

1. Identify the emission skill for the artefact (from the `draft_skill` field in the run record or the emission task name in the plan).
2. Look up the emission skill in `self_review_map.map`. The mapped value is either:
   - a **scalar** (string): the name of the single review skill expected to be invoked from the emission skill's `## Last step`.
   - a **list** of strings: every review skill in the list is expected to be invoked.

   Branch on type: `isinstance(value, list)` vs scalar. Lists iterate; scalars are treated as a single-element check. (Dict values are out of scope; treat as a schema error.)

3. For each expected review skill name:
   - **Only source**: a matching `<id>_<review_skill_short>.json` under `<run_dir>/**`, produced by an explicit plan task (e.g. `review_comp_reqs`, `grounding_check_comp_reqs`) that ran the review skill. Expected filename shapes: `<id>_review.json` for `pharaoh-req-review`, `<id>_code_grounding.json` for `pharaoh-req-code-grounding-check`, `<id>_diagram_review.json` for `pharaoh-diagram-review`, etc.
   - Load the file. If missing, empty object `{}`, or unparseable → record as uncovered with the specific `expected_review_skill` name.
   - **Never accept "inlined" / "covered in emission skill's Last step" / "semantically satisfied" as completion evidence.** The only evidence is a non-empty JSON file on disk at the expected path. The emission skill's `## Last step` clause is explicitly deferred under plan execution (see `pharaoh-req-from-code` SKILL.md); coverage is determined exclusively by the presence of explicit plan-task output files. An uncovered finding indicates the plan did not schedule the review task, the executor skipped it, or the executor claimed "completed" without producing output (which `pharaoh-execute-plan` Step 4.10 should have already caught as a `reporting_error`, but this check provides a second independent signal).

4. The emission is covered only when **every** expected review skill (all list members, or the single scalar) is invoked AND its produced JSON is non-empty. Missing one out of N list members fails, with the missing entry named in `uncovered[].expected_review_skill`.

Backward compatibility: existing scalar mappings (e.g. `pharaoh-req-draft: pharaoh-req-review`) continue to pass under the same check — the scalar is treated as a one-element list.

Use `self_review_map` to label `expected_review_skill` in the uncovered entries. When multiple review skills are expected, emit one `uncovered` entry per missing review skill so the caller sees every missing pair separately.

## Composition

Called by `pharaoh-quality-gate` when `required_checks` contains `self_review_coverage: true`.

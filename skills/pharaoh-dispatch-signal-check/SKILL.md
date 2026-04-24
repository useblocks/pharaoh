---
name: pharaoh-dispatch-signal-check
description: Use when verifying that a plan's declared `execution_mode` matches observed subagent artefacts in `runs/`. Detects the "LLM-executor collapsed subagents into inline" failure class observed during dogfooding. One mechanical structural check.
---

# pharaoh-dispatch-signal-check

## When to use

Invoke from `pharaoh-quality-gate.required_checks` on any plan with `execution_mode: subagents` in any task. Compares declared mode against presence of per-task artefacts in `runs/`. Returns pass/fail + a list of tasks whose declared mode was not honoured.

Do NOT use to enforce dispatch at runtime — that is `pharaoh-execute-plan`. This skill observes after the fact.

## Atomicity

- (a) Indivisible: one plan.yaml + one runs directory in → pass/fail + mismatch list out. No retry, no dispatch, no re-execution.
- (b) Input: `{plan_path: str, runs_path: str}`. Output: JSON `{passed: bool, mismatches: list[{task_id, declared, observed}]}`.
- (c) Reward: fixtures in `pharaoh-validation/fixtures/pharaoh-dispatch-signal-check/`:
  1. `match/`: plan declares `subagents` for two tasks, `runs/task_1/return.json` and `runs/task_2/return.json` both exist → matches `expected-match-pass.json` (`passed: true, mismatches: []`).
  2. `parallel-declared-inline-observed/`: plan declares `subagents`, runs only has `runs/aggregated.json` (no per-task files) → matches `expected-collapsed-fail.json` (`passed: false`, `mismatches` names the task, `observed: "inline"`).
  3. `inline-declared-parallel-observed/`: plan declares `inline`, runs has per-task files anyway → passed: true (over-dispatch is not a failure, only under-dispatch is).
  4. Idempotent.
  
  Pass = all 4.
- (d) Reusable by any plan-executing flow.
- (e) Read-only.

## Input

- `plan_path`: absolute path to `plan.yaml`. Accepts the full schema enum `execution_mode ∈ {inline, subagents, family-bundle, ask}` declared in `pharaoh-execute-plan/schema.md`. Default `ask` if omitted (per schema). This skill only enforces its detection rule on tasks with `execution_mode == subagents`; `inline`, `family-bundle`, and `ask` modes are skipped (no check).
- `runs_path`: absolute path to the plan's runs directory. Convention: `<project_root>/.pharaoh/runs/<run_id>/`.

## Output

```json
{
  "passed": false,
  "mismatches": [
    {
      "task_id": "reqs_from_code",
      "declared": "subagents",
      "observed": "inline",
      "evidence": "expected per-item return.json under runs/reqs_from_code/; found aggregated.json at runs/ root instead"
    }
  ]
}
```

## Detection rule

For each task `T` in the plan with `execution_mode: subagents` and a non-empty `foreach`:

- **Expected shape:** at least `len(foreach)` return artefacts under `<runs_path>/<T.id>/`. Canonical form: per-item subdirectories `task_1/`, `task_2/`, ..., each with a `return.json`.
- **Collapse patterns that fail this check:**
  1. Only `<runs_path>/<T.id>/return.json` exists (single aggregated file under a task-named subdir, no per-item split).
  2. `<runs_path>/aggregated.json` exists at the runs root with no `<T.id>/` subdirectory (flat collapse, as seen in an earlier dogfooding iteration).
  3. Any other pattern with fewer artefacts than `len(foreach)` items.
- The `evidence` field in a mismatch entry names the concrete pattern observed ("single return.json under task subdir", "aggregated.json at the runs root", "N artefacts found, expected M").

For each task `T` with `execution_mode ∈ {inline, family-bundle, ask}`:

- No check. These modes have different (or user-resolved) dispatch semantics that this skill does not model; under-dispatch detection here would produce false positives.

## Composition

Called by `pharaoh-quality-gate` when `required_checks` contains `dispatch_signal_matches_plan: true`. Never called directly.

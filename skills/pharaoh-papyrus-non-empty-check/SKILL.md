---
name: pharaoh-papyrus-non-empty-check
description: Use when verifying that a Papyrus workspace actually received writes during a plan run. Single mechanical check — counts directives across `.papyrus/memory/*.rst` and returns pass/fail against a configured minimum. Wired into `pharaoh-quality-gate` to detect the "LLM-executor skipped the atomic Papyrus writes" failure class observed in prior dogfooding.
---

# pharaoh-papyrus-non-empty-check

## When to use

Invoke from `pharaoh-quality-gate.required_checks` on any plan that declared Papyrus writes (every plan produced by `pharaoh-write-plan` where `preseed_papyrus: true`). Returns `{passed: bool, actual_count: int, required_min: int}` so the gate can decide.

Do NOT use to read or interpret memory content — that is `papyrus-query` / `pharaoh-context-gather`. This skill only counts.

## Atomicity

- (a) Indivisible: one workspace path + one minimum count in → one pass/fail + actual count out. No memory classification, no dedup check, no content inspection.
- (b) Input: `{workspace_path: str, required_min: int}`. Output: JSON `{passed: bool, actual_count: int, required_min: int, workspace_path: str}`.
- (c) Reward: fixtures `pharaoh-validation/fixtures/pharaoh-papyrus-non-empty-check/`:
  1. `empty-workspace/` (7 `.rst` files, only headers, 0 directives) + `required_min: 1` → matches `expected-empty-fail.json` (`passed: false, actual_count: 0`).
  2. `populated-workspace/` (facts.rst with 3 `.. fact::` directives) + `required_min: 1` → matches `expected-populated-pass.json` (`passed: true, actual_count: 3`).
  3. Missing `.papyrus/` directory under workspace_path → `passed: false, actual_count: 0, note: "no papyrus workspace"` (same shape, extra field).
  4. Idempotent: same inputs produce same output.
  
  Pass = all 4.
- (d) Reusable by any composition that declared Papyrus writes.
- (e) Read-only. No side effects.

## Input

- `workspace_path`: absolute path to a directory containing `.papyrus/memory/*.rst`. If the directory does not exist, check returns `passed: false, actual_count: 0, note: "no papyrus workspace"`.
- `required_min`: integer ≥ 0. Minimum number of directives (lines matching `^\.\.\s+[a-z_]+::`) across all `.papyrus/memory/*.rst` files summed together.

## Output

```json
{
  "passed": true,
  "actual_count": 3,
  "required_min": 1,
  "workspace_path": "/absolute/path/to/workspace",
  "note": null
}
```

On missing workspace:

```json
{
  "passed": false,
  "actual_count": 0,
  "required_min": 1,
  "workspace_path": "/absolute/path/to/workspace",
  "note": "no papyrus workspace"
}
```

## Counting rule

```bash
grep -rEh '^\.\.\s+[a-z_]+::' <workspace_path>/.papyrus/memory/*.rst 2>/dev/null | wc -l
```

An RST directive line must match `^\.\.\s+[a-z_]+::`. Header underlines (`====`) and blank lines do not count.

## Composition

Called by `pharaoh-quality-gate` when `required_checks` contains `papyrus_non_empty: {required_min: N}`. Never called directly by user-facing flows.

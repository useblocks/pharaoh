---
name: pharaoh-quality-gate
description: Use when running the final validation step of any Pharaoh composition that emits artefacts (reqs, features, architecture elements). Consumes an aggregated review+mece+coverage summary plus a gate spec; returns pass/fail with named breaches. Never produces summaries itself — thin gate layer over upstream atomic checkers.
---

# pharaoh-quality-gate

## When to use

Invoke as the terminal task of a plan (emitted by `pharaoh-write-plan`, executed by `pharaoh-execute-plan`) after `pharaoh-req-review`, `pharaoh-mece`, and `pharaoh-coverage-gap` tasks have produced their reports. This skill aggregates their findings against configured thresholds and decides whether the run may declare itself "complete". Without this gate, a plan that emits N artefacts with zero quality checks can return success on `sphinx-build exit 0` alone — the exact failure mode observed during dogfooding.

Do NOT use to produce the reports it consumes — that is upstream atomic skills. Do NOT use to halt execution — this skill returns pass/fail; the plan's `on_fail` policy or the human decides what to do with that.

## Atomicity

- (a) Indivisible — one artefacts summary + one gate spec + one project_root in → one pass/fail report out. No new review judgment, no need-file reads, no MECE analysis. Pure threshold check.
- (b) Input: `{artefacts_summary_path: str, gate_spec_path: str, project_root: str}`. Output: JSON `{pass: bool, breaches: list[str], report_path: str}`.
- (c) Reward: fixtures `pharaoh-validation/fixtures/pharaoh-quality-gate/`:
  1. `input_artefacts.yaml` + `gate_spec.yaml` where all thresholds pass → output `pass: true`, `breaches: []`, report written to `<project_root>/.pharaoh/quality-gate-report-<timestamp>.yaml` matching `expected_report_pass.yaml` (timestamp masked).
  2. Same input_artefacts with a gate_spec variant where `testability_fail_rate_max: 0.20` but observed is `0.25` → `pass: false`, `breaches` names that threshold, report matches `expected_report_fail.yaml`.
  3. Idempotent: same inputs produce same output content (up to timestamp).
  4. Missing `artefacts_summary_path` → FAIL.
  5. `gate_spec.invariants.self_review_coverage.enabled: true` + runs path where one artefact is missing its review → `pass: false`, `breaches` includes entry naming the specific artefact and referring to `pharaoh-self-review-coverage-check` output. Same structure for `papyrus_non_empty` and `dispatch_signal_matches_plan`.

  Gate aggregates by calling each configured invariant check as a separate delegated skill, never duplicating the check logic itself — atomicity (a) preserved.

  Pass = all 5.
- (d) Reusable by any composition skill that has upstream review/mece/coverage reports.
- (e) Composable: composition skills invoke this at end; this skill never calls composition or atomic skills back.

## Input

- `artefacts_summary_path` (optional on plans that ran no review/mece/coverage tasks): absolute path to a YAML document produced by aggregating `pharaoh-req-review`, `pharaoh-mece`, and `pharaoh-coverage-gap` reports. Must parse via `yaml.safe_load`. Expected shape:
  ```yaml
  review_axis_fail_rates:
    <axis_name>: <float 0..1>
    ...
  duplicate_rate: <float 0..1>
  orphan_rate: <float 0..1>
  unverified_rate: <float 0..1>
  ```
- `gate_spec_path` (optional): absolute path to a YAML document declaring thresholds. Shape:
  ```yaml
  thresholds:
    review_axis_fail_rate_max: <float 0..1>
    duplicate_rate_max: <float 0..1>
    orphan_rate_max: <float 0..1>
    unverified_rate_max: <float 0..1>
    diagram_lint_errors_max: <int>   # default 0; any error finding breaches
    sampling:
      method: stratified
      per_feat_min: <int>
      per_feat_fraction: <float 0..1>
  ```
- `diagram_lint_findings` (optional, inline): list of finding objects as produced by `pharaoh-diagram-lint`. Each entry matches the shape `{file, line, renderer, block_index, parser_exit_code, parser_stderr, severity}`. Passed by ref from the plan (e.g. `diagram_lint_findings: ${diagram_lint.findings}`), not via file path. When absent, diagram lint is assumed not run and no diagram breach is evaluated.
- `diagram_lint_status` (optional, inline): one of `"pass" | "fail" | "degraded"` as reported by `pharaoh-diagram-lint`. Used by the report's `diagram_lint` section for transparency (a `degraded` status surfaces as a warning in the report, not a breach).
- `project_root`: absolute path used to resolve the report output location (`<project_root>/.pharaoh/quality-gate-report-<timestamp>.yaml`).

### Invariants

Invariant checks are delegated to atomic check skills. Added to close the "skipped atomic step" class of failure observed during dogfooding, plus the structural-lint gaps (ID convention, link coverage, status lifecycle, metadata fields) surfaced by prior catalogue reviews.

```yaml
# gate_spec.yaml — invariants block
invariants:
  papyrus_non_empty:
    enabled: true            # default true when preseed_papyrus was used; false otherwise
    required_min: 1          # minimum directive count across .papyrus/memory/*.rst
  dispatch_signal_matches_plan:
    enabled: true            # default true
  self_review_coverage:
    enabled: true            # default true
    self_review_map_path: skills/shared/self-review-map.yaml   # resolved relative to pharaoh/
  id_convention_consistent:
    enabled: true            # default true when id-conventions.yaml exists
    id_conventions_path: .pharaoh/project/id-conventions.yaml
    needs_json_path: docs/_build/needs/needs.json
  link_types_covered:
    enabled: true            # default true when artefact-catalog.yaml declares required_links
    artefact_catalog_path: .pharaoh/project/artefact-catalog.yaml
    needs_json_path: docs/_build/needs/needs.json
  status_lifecycle_healthy:
    enabled: false           # default false (advisory); release pipelines override to true
    workflow_path: .pharaoh/project/workflows.yaml
    needs_json_path: docs/_build/needs/needs.json
    enforce: true            # release-gate only — binary pass/fail on zero drafts
  metadata_fields_present:
    enabled: true            # default true when artefact-catalog.yaml declares required_metadata_fields
    artefact_catalog_path: .pharaoh/project/artefact-catalog.yaml
    needs_json_path: docs/_build/needs/needs.json
  api_coverage_clean:
    enabled: true            # default true when any source file under source_doc tree is declared
    needs_json_path: docs/_build/needs/needs.json
    source_file: null        # resolved per-file by the plan's scatter-gather; null here means "no default — template must supply"
    language: auto
  task_output_present:
    enabled: true            # default true — independent second signal against "completed but no output" tasks
    report_path: .pharaoh/runs/<latest>/report.yaml
    workspace_dir: .pharaoh/runs/<latest>
```

Every new key follows the same pattern as the existing three: a boolean `enabled` plus whatever paths the delegated check needs. Adding a future invariant is a config-only change to this block plus one row in the delegation table below.

## Invariant delegation

For every key under `gate_spec.invariants.*` where `enabled: true`, the gate invokes the correspondingly named atomic check:

| Invariant key                   | Delegated skill                            | Pass requirement                                             |
| ------------------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| `papyrus_non_empty`             | `pharaoh-papyrus-non-empty-check`          | `passed == true`                                             |
| `dispatch_signal_matches_plan`  | `pharaoh-dispatch-signal-check`            | `passed == true`                                             |
| `self_review_coverage`          | `pharaoh-self-review-coverage-check`       | `passed == true`                                             |
| `id_convention_consistent`      | `pharaoh-id-convention-check`              | `overall == "pass"`                                          |
| `link_types_covered`            | `pharaoh-link-completeness-check`          | `overall == "pass"`                                          |
| `status_lifecycle_healthy`      | `pharaoh-status-lifecycle-check`           | `overall == "pass"` (release-gate only; `enforce=true` is typically supplied by the release pipeline) |
| `metadata_fields_present`       | `pharaoh-output-validate` (graph mode)     | every need carries the tailored `required_metadata_fields` for its type (delegated atom returns `valid == true`) |
| `api_coverage_clean`            | `pharaoh-api-coverage-check`               | `overall ∈ {"pass", "skipped"}`; invoked per source file, aggregated pass = every behavioral file has both a citing CREQ and every raised exception class named in some CREQ, non-behavioral files are skipped |
| `task_output_present`           | inline check (no delegate) — re-runs `pharaoh-execute-plan` Step 4.10 audit against `report_path` + `workspace_dir` | every task with `status: completed` in the report has a non-empty artefact or `return.json` on disk at the declared path; any `reporting_error` status fails the gate |

Each delegated check returns either `{passed: bool, ...}` or the atom's native `{overall: "pass"|"fail", ...}` / `{valid: bool, ...}` shape. The gate normalises each return against the pass requirement in the table and, on failure, merges the atom's breach fields into its top-level `breaches` list under a namespaced prefix (`invariant.<invariant_key>.<field>`). This keeps the gate itself a pure aggregator — atomicity (a) is preserved because the check logic lives in the delegated skills, not here.

`metadata_fields_present` delegates to the existing `pharaoh-output-validate` atom invoked in `mode: "graph"` (see that skill's `## Graph mode`). The tailored `required_metadata_fields` list is declared per-type in `artefact-catalog.yaml`; empty list disables the check for that type, absent key is treated as empty. No new atom is introduced for this invariant — graph mode is a second input-shape on the existing block-validator.

If a delegated check is not yet implemented in the skill tree, the gate records a warning in the report but does not fail — so that adding new invariants in future is a config-only change.

## Output

```json
{
  "pass": false,
  "breaches": [
    "review_axis 'testability' fail rate 0.25 exceeds 0.20",
    "orphan_rate 0.02 exceeds 0.00"
  ],
  "report_path": "/abs/path/.pharaoh/quality-gate-report-2026-04-20T14:03:12Z.yaml"
}
```

On `pass: true`, `breaches` is `[]` but the report file is still written.

## Process

### Step 1: Load inputs

Read `artefacts_summary_path` (if provided) and `gate_spec_path` (if provided) via `yaml.safe_load`. If `artefacts_summary_path` is provided but the file is missing or malformed, FAIL naming the path. Same for `gate_spec_path`. When both are absent (plan did not run review/mece/coverage), the gate degrades to a diagram-lint-only pass/fail and `thresholds_evaluated` in the report will be empty for the review/mece/coverage axes.

### Step 2: Check each threshold

For each threshold in `gate_spec.thresholds` (if gate spec loaded):

- `review_axis_fail_rate_max`: iterate `artefacts_summary.review_axis_fail_rates`. For each axis where observed > max, add `"review_axis '<axis>' fail rate <observed> exceeds <max>"` to breaches.
- `duplicate_rate_max`: if observed > max, add breach.
- `orphan_rate_max`: if observed > max, add breach.
- `unverified_rate_max`: if observed > max, add breach. If max is 1.00, this threshold is inactive (skip — it's a no-op).

Sampling thresholds (`per_feat_min`, `per_feat_fraction`) are informational — they constrain upstream sampling in `pharaoh-req-review`, not checks here. Do not evaluate.

### Step 2.5: Check diagram-lint findings (if provided)

If `diagram_lint_findings` is non-null, count findings with `severity == "error"`. Compare against `gate_spec.thresholds.diagram_lint_errors_max` (default `0`):

- `error_count > max` → add breach `"diagram_lint emitted <error_count> parser-error finding(s), exceeds max <max>"` followed by one sub-breach per finding of shape `"diagram_lint: <file>:L<line> (<renderer>) — <parser_stderr first 120 chars>"`.

If `diagram_lint_status == "degraded"`, add a WARNING (not a breach) to the report: `"diagram_lint ran in degraded mode — at least one renderer CLI was missing; lint coverage is incomplete"`. Warnings surface in the report's `warnings` field but do not flip `pass` to `false`.

### Step 3: Compute pass

`pass = len(breaches) == 0`.

### Step 4: Write report

Write a full report to `<project_root>/.pharaoh/quality-gate-report-<iso8601_timestamp>.yaml` with:

```yaml
timestamp: <iso8601>
pass: <bool>
breaches: [...]
warnings: [...]       # non-breach issues (e.g. diagram_lint degraded mode)
thresholds_evaluated:
  <threshold_name>: {max: <float>, observed: <float>}
  ...
diagram_lint:         # omit this section if diagram_lint_findings was null
  status: <"pass"|"fail"|"degraded">
  errors_count: <int>
  findings:
    - {file, line, renderer, block_index, parser_exit_code, parser_stderr, severity}
    ...
inputs:
  artefacts_summary_path: <abs_path or null>
  gate_spec_path: <abs_path or null>
  diagram_lint_findings_count: <int>
```

Create `.pharaoh/` directory if it does not exist.

### Step 5: Return

Return the JSON object. `report_path` is the absolute path of the file written in Step 4.

## Failure modes

- `artefacts_summary_path` missing or unparseable → FAIL.
- `gate_spec_path` missing or unparseable → FAIL.
- `project_root/.pharaoh/` unwritable → FAIL.

## Non-goals

- Does not produce review / mece / coverage reports — those are `pharaoh-req-review`, `pharaoh-mece`, `pharaoh-coverage-gap`.
- Does not DECIDE thresholds — that's the gate spec authored by the project.
- Does not HALT anything — returns pass/fail; the orchestrator decides.
- No tiered thresholds (e.g. "soft" and "hard" gates) — everything is a hard threshold.

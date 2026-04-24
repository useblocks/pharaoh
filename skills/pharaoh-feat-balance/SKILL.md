---
name: pharaoh-feat-balance
description: Use when a plan emitted by `pharaoh-write-plan` has completed its feature + comp_req emission and you need to check for granularity skew — features with too many reqs (under-decomposed feature model), too few (over-decomposed), fused sub-features (generic names like "utilities"), or redundancy (symmetric import/export pairs). Reports health and suggestions; does not mutate.
---

# pharaoh-feat-balance

## When to use

Invoke after a composition emits feats + comp_reqs, before running `pharaoh-quality-gate`, to catch granularity issues that quality-gate thresholds don't cover. Two typical failure shapes: a feat with an outsized CREQ count (the feat spans multiple capabilities and should be split) and a feat whose title contains a "utilities" / "misc" / "helpers" smell (two unrelated subcommands fused under one name). This skill surfaces both.

Do NOT use to reshape the feature set — it only reports. Caller acts on suggestions manually.

## Atomicity

- (a) Indivisible — one distribution in → one report out. No mutations. No parallel fan-out.
- (b) Input: `{distribution_path: str, thresholds?: {max_reqs_per_feat: int, min_reqs_per_feat: int, name_smell_patterns: list[str], redundancy_title_overlap_min: float, redundancy_count_tolerance: float}}`. Output: YAML report with summary, outliers, redundancy_candidates, overall_health. Defaults: max=15, min=3, name_smell=["utilities","helpers","misc","other","general"], title_overlap=0.5, count_tolerance=0.20.
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-feat-balance/input_distribution.yaml` modelled on a skewed-distribution example. Skill run against it with defaults produces output byte-exact matching `expected_output_skewed.yaml`:
  - `FEAT_reqif_export` flagged `too_many` (19 > 15).
  - `FEAT_jama_utilities` flagged `fused_subfeatures` (title matches smell pattern).
  - `(FEAT_csv_export, FEAT_csv_import)` flagged as redundancy candidate (symmetric import/export with matching counts).
  - `overall_health: "skewed"` (any flag = skewed).
- (d) Reusable on any feature catalogue.
- (e) Composable: never calls other skills.

## Input

- `distribution_path`: absolute path to a YAML file containing the feature distribution. Expected shape:
  ```yaml
  features:
    - feat_id: FEAT_csv_export
      title: "CSV Export"
      reqs_count: 12
    - feat_id: FEAT_reqif_export
      title: "ReqIF Export"
      reqs_count: 19
    ...
  ```
- `thresholds` (optional): override defaults. Partial override supported (missing keys use defaults).

## Output

```yaml
summary:
  feat_count: <int>
  total_reqs: <int>
  mean_reqs_per_feat: <float>
  median: <int>
  min: <int>
  max: <int>
  stdev: <float>

outliers:
  - feat_id: <id>
    reqs_count: <int>
    flag: too_many | too_few | fused_subfeatures
    suggestion: <string>

redundancy_candidates:
  - feats: [<id1>, <id2>]
    reason: <string>

overall_health: healthy | skewed | critical
```

## Process

### Step 1: Load + compute summary

Read `distribution_path` via `yaml.safe_load`. Compute `feat_count`, `total_reqs`, `mean`, `median`, `min`, `max`, `stdev` across `features[*].reqs_count`. Round mean/stdev to one decimal.

### Step 2: Flag outliers

For each feature:
- If `reqs_count > thresholds.max_reqs_per_feat` (default 15) → flag `too_many`. Suggestion: `"Consider splitting: <N> reqs suggests the feature spans multiple distinct capabilities. Look for natural boundaries (e.g. <hint based on title>)."`
- If `reqs_count < thresholds.min_reqs_per_feat` (default 3) → flag `too_few`. Suggestion: `"Feature has only <N> req(s) — verify it's a distinct capability and not a stub. Consider merging into a parent feature if the scope is thin."`
- If feature title (lowercased) matches any `thresholds.name_smell_patterns` (default `["utilities","helpers","misc","other","general"]`) as a substring → flag `fused_subfeatures`. Suggestion: `"Feature title <title> is a code smell — 'utilities' and similar names often lump unrelated capabilities. Consider splitting by the specific capabilities it includes."`

One feature may carry multiple flags — emit one outlier entry per flag.

### Step 3: Detect redundancy candidates

For each pair of features `(A, B)` where A != B:
- Compute title-token overlap: tokenize both titles on whitespace/punctuation, lowercase; `overlap = len(common_tokens) / len(tokens_A ∪ tokens_B)`.
- Compute count ratio: `ratio = min(A.count, B.count) / max(A.count, B.count)`.
- If `overlap >= thresholds.redundancy_title_overlap_min` (default 0.5) AND `ratio >= (1 - thresholds.redundancy_count_tolerance)` (default tolerance 0.20 → ratio ≥ 0.80) → add to `redundancy_candidates`.

Deduplicate by sorting the pair (`[A.id, B.id]` lexicographic).

For each candidate, compose a reason: `"Same title-token overlap (<overlap:.0%>), symmetric counts (<A.count> vs <B.count>). Consider <merged_name>."` where `merged_name` strips the differing token (e.g. `csv_export` + `csv_import` → `csv_exchange`).

### Step 4: Determine overall_health

- `healthy`: zero outliers AND zero redundancy_candidates.
- `skewed`: at least one outlier OR redundancy_candidate.
- `critical`: > 25% of features flagged (outliers only; redundancy does not count toward this).

### Step 5: Return

Return the YAML report.

## Failure modes

- `distribution_path` not readable → FAIL.
- Distribution parses but has no `features` key or empty list → FAIL.

## Non-goals

- No mutation of the feature set.
- No re-draft suggestions — this skill describes the shape problem, not the fix.
- No cross-project comparison — one distribution per invocation.

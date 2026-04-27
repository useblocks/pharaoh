---
name: pharaoh-process-audit
description: Use when running a full-corpus audit against a sphinx-needs project. Orchestrates pharaoh-coverage-gap across all gap categories plus cross-artefact consistency checks. Emits a prioritised gap report.
chains_from: []
chains_to: [pharaoh-coverage-gap, pharaoh-standard-conformance]
---

# pharaoh-process-audit

## When to use

Invoke when you want a single, prioritised gap report covering all known gap categories in a
sphinx-needs project in one operation. This skill orchestrates `pharaoh-coverage-gap` across
all 10 categories; it does not detect gaps itself.

**Scope:** one project root → one gap report across all 10 categories.

Do NOT invoke when you want to check a single gap category — use `pharaoh-coverage-gap`
directly. Do NOT invoke when you want indicator-level standard conformance on a single
artefact — use `pharaoh-standard-conformance`.

> This is a compositional orchestrator. Atomicity criterion (a) does not apply: by design
> it delegates to `pharaoh-coverage-gap` for each category. Scope is bounded to
> "one project → one full-corpus gap report".

---

## Inputs

- **project_root**: path to the sphinx-needs project (must contain `.pharaoh/project/` tailoring
  and a built `needs.json` under `docs/_build/needs/needs.json` or equivalent)

---

## Outputs

A single JSON document — no prose wrapper. Shape:

```json
{
  "project_path": "examples/my-project",
  "needs_total": 401,
  "gaps": [
    {
      "category": "unverified_req",
      "severity": "high",
      "count": 3,
      "exemplars": ["gd_req__power_budget_monitoring", "gd_req__impl_complexity_analysis"],
      "detection_rule": "gd_req needs with no tc__* linking to them via :verifies:"
    }
  ],
  "summary_by_severity": {
    "high": 2,
    "medium": 5,
    "low": 1
  },
  "recommended_next_actions": [
    "Address 3 unverified_req gaps: add :verification: fields and corresponding tc__ needs.",
    "Fix 2 broken_back_link gaps before next build: link targets do not exist in needs.json."
  ]
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `project_path` | string | Echoes `project_root` |
| `needs_total` | integer | Total number of needs in needs.json |
| `gaps` | array | One entry per category where `match_count > 0`, sorted by severity |
| `gaps[].category` | string | Gap category name (one of 10) |
| `gaps[].severity` | `"high"` / `"medium"` / `"low"` | Highest severity_hint seen in that category |
| `gaps[].count` | integer | Total matches for that category |
| `gaps[].exemplars` | array | Up to 3 representative need IDs (highest-severity first) |
| `gaps[].detection_rule` | string | One-sentence description from `pharaoh-coverage-gap` |
| `summary_by_severity` | object | Count of categories (not needs) at each severity level |
| `recommended_next_actions` | array | Up to 5 concrete actions, highest-priority first |

Categories with zero matches are omitted from `gaps`.

---

## Process

### Step 0: Validate inputs

Confirm `project_root` is provided and exists. Confirm `.pharaoh/project/` directory is
present. If tailoring is missing, FAIL before running any sub-skill:

```
FAIL: .pharaoh/project/ not found at <project_root>/.pharaoh/project/.
Run pharaoh-tailor-detect → pharaoh-tailor-fill first.
```

Find needs.json: check `<project_root>/docs/_build/needs/needs.json`, then
`<project_root>/_build/needs/needs.json`. If not found:

```
FAIL: needs.json not found at expected paths under <project_root>.
Rebuild the Sphinx project first: sphinx-build docs/ docs/_build/
```

Record `needs_total` from the top-level count in needs.json.

---

### Step 1: Run pharaoh-coverage-gap for each category

Invoke `pharaoh-coverage-gap` once per category, in this order:

1. `broken_back_link`
2. `schema_violation`
3. `wrong_prefix_id`
4. `orphan_arch`
5. `unverified_req`
6. `invalid_lifecycle_transition`
7. `missing_fmea`
8. `stale_review`
9. `duplicate_req`
10. `contradictory_req_pair`

The order is deterministic → results ordered by cheapest-to-detect first (low
`false_positive_risk` categories first; expensive NLI/embedding categories last).

For each category, pass `project_root` and `category`. Capture the returned JSON.

If a sub-skill returns a FAIL rather than a JSON result, record the category as:

```json
{
  "category": "<category>",
  "severity": "high",
  "count": -1,
  "exemplars": [],
  "detection_rule": "FAILED: <fail message>"
}
```

Continue with remaining categories — do not abort the full audit on one category failure.

---

### Step 2: Aggregate results

For each category result:

- If `match_count == 0`: skip (omit from `gaps`).
- If `match_count > 0`: construct a gap entry:
  - `severity` = highest `severity_hint` seen across all matches in that category
  - `exemplars` = first 3 `need_id` values from `matches` (already ordered high→low)
  - `detection_rule` from the sub-skill result

---

### Step 3: Sort and summarise

Sort `gaps` by severity: `high` first, then `medium`, then `low`. Within each tier, preserve
the detection order from Step 1.

Compute `summary_by_severity` by counting entries at each severity tier.

---

### Step 4: Generate recommended next actions

For the top-5 highest-severity gaps, generate one concrete action each. Each action must:
- Name the category
- State the count
- Suggest the most direct remediation (e.g. "add :verification: field", "fix link target",
  "split requirement body")

If fewer than 5 gaps exist, generate one action per gap. If zero gaps, set
`recommended_next_actions: ["No gaps detected — corpus is clean."]`.

---

### Step 5: Emit JSON

Emit the single JSON document. No prose before or after.

---

## Guardrails

**G1 — Missing tailoring**

`.pharaoh/project/` absent → FAIL before any sub-skill runs (Step 0).

**G2 — Missing needs.json**

needs.json not found → FAIL before any sub-skill runs (Step 0).

**G3 — Sub-skill failure**

A single `pharaoh-coverage-gap` failure does not abort the audit. Record as count -1 and
continue (Step 1). At audit completion, if any categories failed, append a note:

```
NOTE: <n> categories failed during detection — results for those categories are incomplete.
```

**G4 — Corrupted needs.json**

If needs.json is present but cannot be parsed as JSON:

```
FAIL: needs.json at <path> is not valid JSON.
Check for incomplete builds or file-system errors.
```

---

## Advisory chain

After the gap report, if `gaps` is non-empty:

- For each `high`-severity gap, append after the JSON:
  ```
  Run `pharaoh-coverage-gap <project_root> <category>` for the full match list.
  ```
- For standard conformance on individual flagged artefacts, suggest `pharaoh-standard-conformance`.

---

## Worked example

**Input:** `project_root = examples/my-project`

**Step 0:** `.pharaoh/project/` found; needs.json found with 401 needs total.

**Step 1 — detection results (condensed):**

| Category | match_count | highest severity |
|---|---|---|
| broken_back_link | 2 | high |
| schema_violation | 3 | medium |
| wrong_prefix_id | 0 | — |
| orphan_arch | 1 | high |
| unverified_req | 3 | high |
| invalid_lifecycle_transition | 0 | — |
| missing_fmea | 2 | medium |
| stale_review | 4 | medium |
| duplicate_req | 1 | medium |
| contradictory_req_pair | 0 | — |

**Step 2:** 7 categories with matches; 3 categories clean.

**Step 3:** sorted by severity; `summary_by_severity` computed.

**Step 4:** top-5 actions generated for high and medium gaps.

**Step 5 output:**

```json
{
  "project_path": "examples/my-project",
  "needs_total": 401,
  "gaps": [
    {
      "category": "broken_back_link",
      "severity": "high",
      "count": 2,
      "exemplars": ["arch__diag_subsystem", "tc__power_budget_001"],
      "detection_rule": "needs whose :satisfies: or :verifies: target does not exist in needs.json"
    },
    {
      "category": "orphan_arch",
      "severity": "high",
      "count": 1,
      "exemplars": ["arch__legacy_watchdog_module"],
      "detection_rule": "arch needs with no :satisfies: link resolving to a gd_req"
    },
    {
      "category": "unverified_req",
      "severity": "high",
      "count": 3,
      "exemplars": ["gd_req__power_budget_monitoring", "gd_req__impl_complexity_analysis", "gd_req__diag_log_rotation"],
      "detection_rule": "gd_req needs with no tc__* linking to them via :verifies:"
    },
    {
      "category": "stale_review",
      "severity": "medium",
      "count": 4,
      "exemplars": ["gd_req__brake_pedal_response", "gd_req__ecu_reset_recovery", "arch__abs_controller"],
      "detection_rule": "needs with status=inspected but no review record within the last 12 months"
    },
    {
      "category": "missing_fmea",
      "severity": "medium",
      "count": 2,
      "exemplars": ["gd_req__abs_pump_activation", "gd_req__wheel_speed_plausibility"],
      "detection_rule": "gd_req with safety-relevant tag (ASIL-A/B/C/D) but no fmea need referencing them"
    },
    {
      "category": "schema_violation",
      "severity": "medium",
      "count": 3,
      "exemplars": ["gd_req__impl_complexity_analysis", "arch__diag_subsystem", "arch__power_mgmt_module"],
      "detection_rule": "needs missing required_fields listed in artefact-catalog.yaml for their type"
    },
    {
      "category": "duplicate_req",
      "severity": "medium",
      "count": 1,
      "exemplars": ["gd_req__ecu_watchdog_timeout"],
      "detection_rule": "pair of gd_req bodies with cosine distance < 0.15"
    }
  ],
  "summary_by_severity": {
    "high": 3,
    "medium": 4,
    "low": 0
  },
  "recommended_next_actions": [
    "Fix 2 broken_back_link gaps: verify targets arch__diag_subsystem and tc__power_budget_001 exist in needs.json or correct the link values.",
    "Resolve 1 orphan_arch gap: add :satisfies: link to arch__legacy_watchdog_module pointing to its parent gd_req.",
    "Add verification for 3 unverified_req needs: create tc__ needs with :verifies: gd_req__power_budget_monitoring, gd_req__impl_complexity_analysis, gd_req__diag_log_rotation.",
    "Re-inspect 4 stale_review needs or update :inspection_record: dates to reflect current review status.",
    "Create fmea entries for 2 ASIL-tagged requirements: gd_req__abs_pump_activation and gd_req__wheel_speed_plausibility."
  ]
}
```

Run `pharaoh-coverage-gap examples/my-project broken_back_link` for the full match list.
Run `pharaoh-coverage-gap examples/my-project orphan_arch` for the full match list.
Run `pharaoh-coverage-gap examples/my-project unverified_req` for the full match list.

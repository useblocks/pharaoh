---
name: pharaoh-coverage-gap
description: Use when detecting one gap category (orphan / unverified / duplicate / contradictory / lifecycle / ...) in a sphinx-needs corpus. Returns ordered list of needs falling into that gap.
chains_from: [pharaoh-process-audit]
chains_to: []
---

# pharaoh-coverage-gap

## When to use

Invoke when you want to scan a sphinx-needs corpus for a single, named gap category and get
back the list of needs that fall into it.

**One category per invocation.** For a full-corpus audit across all 10 gap categories at once,
use `pharaoh-process-audit` instead.

Do NOT use to fix the gaps — this skill only detects and lists them.

---

## Inputs

- **project_root**: path to the sphinx-needs project (must contain `.pharaoh/project/` tailoring
  and a built `needs.json` under `docs/_build/needs/needs.json` or equivalent)
- **category**: one of the 10 supported gap categories (see Detection rules below)

---

## Outputs

A single JSON document — no prose wrapper. Shape:

```json
{
  "category": "unverified_req",
  "detection_rule": "gd_req needs with no tc__* linking to them via :verifies:",
  "matches": [
    {
      "need_id": "gd_req__abs_pump_activation",
      "evidence": ":verification: field absent; no tc found with :verifies: gd_req__abs_pump_activation",
      "severity_hint": "high"
    }
  ],
  "match_count": 1,
  "false_positive_risk": "low"
}
```

Fields:

| Field | Type | Description |
|---|---|---|
| `category` | string | Echoes the input `category` |
| `detection_rule` | string | One-sentence description of the rule applied |
| `matches` | array | Ordered list of gaps found (most severe / most prominent first) |
| `matches[].need_id` | string | ID of the need falling into the gap |
| `matches[].evidence` | string | Specific observation — what is missing or wrong |
| `matches[].severity_hint` | `"high"` / `"medium"` / `"low"` | Per-match severity for process-audit aggregation |
| `match_count` | integer | `len(matches)` |
| `false_positive_risk` | `"low"` / `"medium"` / `"high"` | Signal reliability flag (see Detection rules) |

---

## Detection rules

### `orphan_arch`

**Rule:** arch needs that have no `:satisfies:` link, or whose `:satisfies:` target does not
resolve to a `gd_req` in needs.json.

**Detection:** For every need of type `arch`, check (a) `:satisfies:` field is present and
non-empty, (b) the resolved need exists in needs.json, (c) the resolved need is of type `gd_req`.
Report any that fail any of (a)–(c).

**false_positive_risk:** `low` — purely link-resolution, no model judgment.

---

### `unverified_req`

**Rule:** `gd_req` needs with no test case pointing to them via `:verifies:`.

**Detection:** Build an inverted index: for each `tc` need, collect need IDs in its `:verifies:`
field. For each `gd_req`, check whether its id appears in this index. Report any `gd_req` that
does not appear.

**false_positive_risk:** `low` — deterministic graph query.

---

### `invalid_lifecycle_transition`

**Rule:** need whose `status` value is not reachable from the previous recorded state per the
`workflows.yaml` state machine.

**Detection:** Read `workflows.yaml` transitions. For each need, check:
- `status` is declared in `lifecycle_states`.
- If the need carries a `previous_status` field (or history metadata), the transition is legal
  per `transitions`. If no history is available, check only that `status` is a declared state.

Report needs with undeclared status values, and — when history is available — needs that
skipped a required intermediate state.

**false_positive_risk:** `medium` — history fields may not be present in all projects; partial
detection when `previous_status` is absent.

---

### `duplicate_req`

**Rule:** pair of `gd_req` bodies with cosine distance < 0.15 (near-identical text).

**Detection:** For each pair of `gd_req` needs, compute the cosine similarity of their body
text (TF-IDF or embedding representation). Flag pairs where cosine distance < 0.15 (similarity
> 0.85). Report the lower-priority need in each pair as the duplicate (the one with the higher
alphabetical id, as a tie-breaker).

**false_positive_risk:** `medium` — embedding/TF-IDF similarity is approximation; near-identical
bodies may be intentional specialisations. Include both need IDs in `evidence` to let the user
decide.

---

### `contradictory_req_pair`

**Rule:** pair of `gd_req` needs where NLI (natural language inference) scores the pair as
"contradiction".

**Detection:** For each pair of `gd_req` body texts, apply NLI entailment check. Flag pairs
where the contradiction label has the highest logit. Report both need IDs in `evidence`.

**false_positive_risk:** `high` — NLI models misfire on domain-specific requirements language.
Always include both full bodies in `evidence` for human review.

---

### `missing_fmea`

**Rule:** `gd_req` needs carrying a safety-relevant tag (any tag matching `ASIL-[ABCD]` or
`safety_goal__*`) but with no `fmea` need referencing them.

**Detection:** For each `gd_req`, check its `tags` field for ASIL or safety-goal markers.
Build an inverted index: for each `fmea` need, collect the IDs in any reference field
(`:parent_id:` or `:satisfies:` or `:id:` prefix `fmea__<req_stem>`). Report any safety-tagged
`gd_req` not covered.

**false_positive_risk:** `low` if ASIL tags are present; `medium` if safety relevance must be
inferred from body text.

---

### `stale_review`

**Rule:** need with `status: inspected` but no review record dated within the last 12 months.

**Detection:** For each need where `status = inspected`, check for a `:reviewed_by:` or
`:inspection_record:` field. If the field contains a date, verify it is within 365 days of
today. If absent or older than 365 days, report as stale.

**false_positive_risk:** `medium` — date parsing depends on the convention used in the field
value; projects with no date convention will show `medium` risk.

---

### `broken_back_link`

**Rule:** need whose `:satisfies:` (or `:verifies:`) target does not exist in needs.json.

**Detection:** For every need that carries a `:satisfies:` or `:verifies:` field, look up each
referenced ID in needs.json. Report any ID that does not resolve.

**false_positive_risk:** `low` — pure existence check.

---

### `schema_violation`

**Rule:** need missing one or more fields listed as `required_fields` in artefact-catalog.yaml
for its type.

**Detection:** For each need, look up its type in artefact-catalog.yaml. Check that every
`required_fields` entry is present and non-empty in the need's field map. Report violations.

**false_positive_risk:** `low` — deterministic field presence check.

---

### `wrong_prefix_id`

**Rule:** need whose `id` does not match the `id_regex` for its type in id-conventions.yaml.

**Detection:** For each need, look up the `id_regex` for its type in id-conventions.yaml. Apply
the regex to the need's `id` field. Report any mismatch.

**false_positive_risk:** `low` — deterministic regex match.

---

## Process

### Step 1: Validate inputs

Confirm `project_root` and `category` are provided. If `category` is not one of the 10
supported values, FAIL:

```
FAIL: unknown category "<value>".
Supported categories: orphan_arch, unverified_req, invalid_lifecycle_transition,
duplicate_req, contradictory_req_pair, missing_fmea, stale_review,
broken_back_link, schema_violation, wrong_prefix_id.
```

---

### Step 2: Load tailoring and needs.json

Read `.pharaoh/project/artefact-catalog.yaml`, `.pharaoh/project/id-conventions.yaml`, and
`.pharaoh/project/workflows.yaml` from `project_root`.

Find needs.json: check `<project_root>/docs/_build/needs/needs.json`, then
`<project_root>/_build/needs/needs.json`. Extract the flat needs ID map.

If needs.json is missing, FAIL with path attempted and rebuild hint.
If tailoring files are missing, FAIL with missing-file name.

---

### Step 3: Apply detection rule

Apply the detection rule for `category` (see Detection rules above) to the full needs map.
Collect all matching need IDs with evidence and severity hints.

For categories that require pairwise comparison (`duplicate_req`, `contradictory_req_pair`):
process all pairs. Log the first occurrence of each pair; do not double-report.

For categories that require external models (cosine similarity, NLI): apply the model; flag
`false_positive_risk` accordingly.

---

### Step 4: Order results

Sort `matches` by severity_hint: `high` first, then `medium`, then `low`. Within each
severity tier, sort alphabetically by `need_id`.

---

### Step 5: Emit JSON

Emit the single JSON document. No prose before or after.

---

## Guardrails

**G1 — Unknown category**

Unsupported `category` value → FAIL (Step 1) with enumerated list. Do not proceed.

**G2 — Missing needs.json**

```
FAIL: needs.json not found at expected paths.
Rebuild the Sphinx project first: sphinx-build docs/ docs/_build/
```

**G3 — Missing tailoring**

```
FAIL: <filename> not found at .pharaoh/project/<filename>.
Run pharaoh-tailor-fill to generate tailoring files.
```

**G4 — Empty corpus**

If needs.json contains zero needs, return:

```json
{
  "category": "<category>",
  "detection_rule": "<rule>",
  "matches": [],
  "match_count": 0,
  "false_positive_risk": "low"
}
```

Do not FAIL — an empty corpus is valid (no gaps by definition).

---

## Advisory chain

`chains_to: []` — this skill is terminal. If `match_count > 0`, append after the JSON:

```
Use `pharaoh-process-audit` to run all 10 gap categories in one pass.
```

---

## Worked example

**Run against the Score project — two categories:**

### Category 1: `unverified_req`

**Inputs:** `project_root = examples/score`, `category = unverified_req`

**Step 2:** tailoring loaded; needs.json found with 185 `gd_req` needs and 63 `tc` needs.

**Step 3:** inverted index built from `tc` `:verifies:` fields. After scanning all 185
`gd_req` ids, 3 are not found in the index:
- `gd_req__impl_complexity_analysis` — no `:verification:` field; no tc found
- `gd_req__power_budget_monitoring` — `:verification:` present but referenced tc not in needs.json
- `gd_req__diag_log_rotation` — no tc with matching `:verifies:`

```json
{
  "category": "unverified_req",
  "detection_rule": "gd_req needs with no tc__* linking to them via :verifies:",
  "matches": [
    {
      "need_id": "gd_req__power_budget_monitoring",
      "evidence": ":verification: tc__power_budget_001 present but tc not found in needs.json (broken link)",
      "severity_hint": "high"
    },
    {
      "need_id": "gd_req__impl_complexity_analysis",
      "evidence": ":verification: field absent; no tc found with :verifies: gd_req__impl_complexity_analysis",
      "severity_hint": "high"
    },
    {
      "need_id": "gd_req__diag_log_rotation",
      "evidence": "no tc found with :verifies: gd_req__diag_log_rotation",
      "severity_hint": "medium"
    }
  ],
  "match_count": 3,
  "false_positive_risk": "low"
}
```

---

### Category 2: `schema_violation`

**Inputs:** `project_root = examples/score`, `category = schema_violation`

**Step 3:** artefact-catalog.yaml loaded. For `gd_req`, required fields are `[id, status, satisfies]`.
After scanning all needs: 1 `gd_req` missing `:satisfies:` field; 2 `arch` needs missing
`:type:` field.

```json
{
  "category": "schema_violation",
  "detection_rule": "needs missing required_fields listed in artefact-catalog.yaml for their type",
  "matches": [
    {
      "need_id": "gd_req__impl_complexity_analysis",
      "evidence": "gd_req required field 'satisfies' is absent",
      "severity_hint": "medium"
    },
    {
      "need_id": "arch__diag_subsystem",
      "evidence": "arch required field 'type' is absent",
      "severity_hint": "medium"
    },
    {
      "need_id": "arch__power_mgmt_module",
      "evidence": "arch required field 'type' is absent",
      "severity_hint": "medium"
    }
  ],
  "match_count": 3,
  "false_positive_risk": "low"
}
```

Use `pharaoh-process-audit` to run all 10 gap categories in one pass.

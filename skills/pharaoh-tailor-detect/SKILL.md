---
name: pharaoh-tailor-detect
description: Use when inspecting a sphinx-needs project to emit a structured report of detected conventions — prefixes, ID regex candidates, separator, lifecycle states, artefact types with observed required/optional fields. Does NOT author tailoring files (see pharaoh-tailor-fill).
chains_to: [pharaoh-tailor-fill, pharaoh-tailor-review]
---

# pharaoh-tailor-detect

## When to use

Invoke when you have a built sphinx-needs project and want to bootstrap tailoring configuration
automatically. This skill reads the `needs.json` index and derives what conventions the project
actually uses — it does not guess, it observes.

Do NOT invoke this skill to author tailoring files — that is `pharaoh-tailor-fill`. Do NOT
invoke this to validate existing tailoring — that is `pharaoh-tailor-review`. This skill only
observes and reports.

---

## Inputs

- **project_dir** (from user): path to the sphinx-needs project root. Must contain a built
  `needs.json` at a discoverable path (see Step 1 for search order).
- No tailoring files required — this skill bootstraps from raw data.

---

## Outputs

A single JSON document — no prose wrapper. Shape:

```json
{
  "prefixes": {
    "gd_req": {
      "count": 185,
      "example_ids": ["gd_req__brake_activation", "gd_req__safety_goal_1"]
    },
    "std_req": {
      "count": 580,
      "example_ids": ["std_req__iso26262__4_3_1", "std_req__aspice__SWE2_BP1"]
    }
  },
  "separator": "__",
  "id_regex_candidate": "^[a-z][a-z_]*__[a-z0-9_]+$",
  "id_regex_exceptions": {
    "std_req": "^std_req__<source>__<UPSTREAM-ID>$ (pattern inferred; verify manually)"
  },
  "lifecycle_states_observed": ["draft", "valid", "inspected"],
  "artefact_types": {
    "gd_req": {
      "observed_fields_required": [
        ["id", 185], ["status", 185], ["satisfies", 184]
      ],
      "observed_fields_optional": [
        ["complies", 173], ["rationale", 42], ["tags", 31], ["verification", 29]
      ],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    },
    "std_req": {
      "observed_fields_required": [
        ["id", 580], ["status", 580]
      ],
      "observed_fields_optional": [
        ["complies", 12], ["tags", 8]
      ],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    }
  },
  "warnings": [
    "std_req IDs do not match the common regex pattern — id_regex_exception recorded"
  ]
}
```

---

## Process

### Step 1: Locate needs.json

Search in order:
1. `<project_dir>/build/needs/needs.json`
2. `<project_dir>/docs/_build/needs/needs.json`
3. `<project_dir>/_build/needs/needs.json`
4. `<project_dir>/bazel-bin/needs_json/_build/needs/needs.json`
5. Any `needs.json` under a `_build` or `build` directory (recursive, first match)

If not found in any location, FAIL:

```
FAIL: needs.json not found under <project_dir>.
Build the project first:
  sphinx-build docs/ docs/_build/       (Sphinx)
  bazel build //...:needs_json          (Bazel)
Then re-run pharaoh-tailor-detect.
```

---

### Step 2: Parse needs.json and extract all needs

Load the JSON file. The top-level structure may be:

```json
{"versions": {"<version>": {"needs": {"<id>": {...}}}}}
```

or a flat `{"needs": {"<id>": {...}}}`. Handle both. Extract the flat map
`id → {id, type, status, <all other fields>}` from the most recent version if versioned.

If the total need count is < 10, FAIL:

```
FAIL: needs.json contains only <N> needs — corpus too small for confident detection.
Pharaoh-tailor-detect requires at least 10 needs to infer reliable conventions.
Populate the project with representative content and rebuild before detecting.
```

---

### Step 3: Detect separator and prefixes

**3a. Determine separator**

Check all IDs for common separator patterns. Test candidates `__`, `_`, `-` in order. The
separator is the string that divides the type prefix from the local-ID part in the majority
of IDs.

Algorithm:
- Split each ID on the candidate separator (max 2 parts).
- The separator is the one for which ≥ 70% of IDs split cleanly into exactly 2 non-empty parts.
- If no candidate achieves 70%, record `"separator": null` and emit a warning.

**3b. Group by prefix**

Using the detected separator, split each ID into `(prefix, local_part)`. Group all IDs by
prefix. For each prefix record:
- `count`: number of needs with this prefix
- `example_ids`: up to 3 representative IDs (first alphabetically)

---

### Step 4: Detect ID regex candidates

**Common regex pattern:** `^[a-z][a-z_]*__[a-z0-9_]+$` (using `__` separator).

For each prefix, test all its IDs against the common pattern.

- If ≥ 95% of a prefix's IDs match the common pattern → record `id_regex_candidate` as the
  common pattern.
- If a prefix has < 95% match rate, inspect the non-matching IDs and construct a
  prefix-specific regex candidate. Record under `id_regex_exceptions`.
- Note the exception with a `(pattern inferred; verify manually)` annotation — do not claim
  certainty about exceptions.

---

### Step 5: Detect lifecycle states

Collect all unique non-empty values of the `status` field across all needs. Record as
`lifecycle_states_observed` sorted alphabetically.

If no need has a `status` field, record `"lifecycle_states_observed": []` and add a warning.

---

### Step 6: Compute field frequencies per prefix

For each prefix-grouped set of needs:

1. Collect all field keys that appear on at least one need in the group (excluding `id` and
   `type` — those are always present structurally).
2. For each field key, count the number of needs in the group that carry a non-empty value.
3. Express as `[field_name, count]` tuples.
4. Split into:
   - `observed_fields_required`: field count / group_size ≥ 0.95
   - `observed_fields_optional`: field count / group_size ≥ 0.20 and < 0.95
5. Include `id` and `status` in `observed_fields_required` always (structural).
6. Sort each list descending by count.

Add `"required_threshold_note": "Field present in >= 95% of instances considered required"` to
each artefact type entry.

---

### Step 7: Compile warnings

Collect any anomalies encountered:
- Prefixes with non-matching ID regex (note which prefix and what fraction matched)
- `status` field absent from entire corpus
- Separator detection fell below 70% threshold
- Any prefix with count == 1 (singleton — may be an outlier, not a real type)

Add all warnings to the top-level `"warnings": [...]` array. If no anomalies, emit `"warnings": []`.

---

### Step 8: Emit JSON

Emit the single JSON document per the Output shape. No prose before or after.

---

## Guardrails

**G1 — needs.json not found**

FAIL with build hint (Step 1). Do not attempt inference without data.

**G2 — Corpus too small**

< 10 total needs → FAIL (Step 2). Field frequencies from tiny samples are not meaningful.

**G3 — No separator detected**

If no separator candidate achieves 70% coverage, record `separator: null` and
`id_regex_candidate: null`, add a warning, and continue — the output is still useful for
`lifecycle_states_observed` and raw prefix counts.

**G4 — Malformed needs.json**

If the JSON is syntactically invalid or the `needs` key is missing, FAIL:

```
FAIL: needs.json is malformed or missing the 'needs' key.
Rebuild the project and retry.
```

---

## Advisory chain

After successfully emitting the report, always advise:

```
Pass this report to `pharaoh-tailor-fill` to author the .pharaoh/project/ tailoring files.
Review the id_regex_exceptions entries manually before proceeding.
```

---

## Worked example

**User input:** `project_dir = /work/eclipse-score`

**Step 1:** `needs.json` found at `/work/eclipse-score/docs/_build/needs/needs.json`.

**Step 2:** 1281 needs loaded. Corpus size check passed.

**Step 3:** Separator `__` achieves 98% clean split. Prefixes detected: `gd_req` (185),
`std_req` (580), `wp` (74), `wf` (79), `gd_chklst` (15), `tc` (348).

**Step 4:** `gd_req`, `wp`, `wf`, `gd_chklst`, `tc` all pass ≥ 95% match on
`^[a-z][a-z_]*__[a-z0-9_]+$`. `std_req` fails — IDs contain uppercase and an extra segment
(e.g. `std_req__iso26262__4_3_1`). Exception recorded.

**Step 5:** Unique status values: `draft`, `inspected`, `valid`.

**Step 6:** For `gd_req` (185 needs): `id` 185/185, `status` 185/185, `satisfies` 184/185
(≥ 95% → required). `complies` 173/185 (93.5% → optional by threshold), `rationale` 42/185,
`tags` 31/185, `verification` 29/185 (all < 95% → optional).

**Step 7:** One warning: `std_req IDs do not match the common regex pattern — id_regex_exception recorded`.

**Step 8 output:**

```json
{
  "prefixes": {
    "gd_req":    {"count": 185, "example_ids": ["gd_req__abs_pump_activation", "gd_req__brake_system_safety"]},
    "gd_chklst": {"count": 15,  "example_ids": ["gd_chklst__functional_safety_req"]},
    "std_req":   {"count": 580, "example_ids": ["std_req__aspice__SWE2_BP1", "std_req__iso26262__4_3_1"]},
    "tc":        {"count": 348, "example_ids": ["tc__abs_pump_001", "tc__brake_coast_002"]},
    "wf":        {"count": 79,  "example_ids": ["wf__brake_system_design"]},
    "wp":        {"count": 74,  "example_ids": ["wp__brake_release_1_0"]}
  },
  "separator": "__",
  "id_regex_candidate": "^[a-z][a-z_]*__[a-z0-9_]+$",
  "id_regex_exceptions": {
    "std_req": "^std_req__<source>__<UPSTREAM-ID>$ (pattern inferred; verify manually)"
  },
  "lifecycle_states_observed": ["draft", "inspected", "valid"],
  "artefact_types": {
    "gd_req": {
      "observed_fields_required": [["id", 185], ["status", 185], ["satisfies", 184]],
      "observed_fields_optional": [["complies", 173], ["rationale", 42], ["tags", 31], ["verification", 29]],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    },
    "std_req": {
      "observed_fields_required": [["id", 580], ["status", 580]],
      "observed_fields_optional": [["complies", 12], ["tags", 8]],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    },
    "tc": {
      "observed_fields_required": [["id", 348], ["status", 348], ["verifies", 345]],
      "observed_fields_optional": [["tags", 87], ["level", 63], ["rationale", 41]],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    },
    "wf": {
      "observed_fields_required": [["id", 79], ["status", 79], ["input", 79], ["output", 79], ["responsible", 77]],
      "observed_fields_optional": [["approved_by", 31], ["supported_by", 28], ["has", 14]],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    },
    "wp": {
      "observed_fields_required": [["id", 74], ["status", 74]],
      "observed_fields_optional": [["tags", 18], ["complies", 11]],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    },
    "gd_chklst": {
      "observed_fields_required": [["id", 15], ["status", 15]],
      "observed_fields_optional": [["tags", 4]],
      "required_threshold_note": "Field present in >= 95% of instances considered required"
    }
  },
  "warnings": [
    "std_req IDs do not match the common regex pattern — id_regex_exception recorded"
  ]
}
```

```
Pass this report to `pharaoh-tailor-fill` to author the .pharaoh/project/ tailoring files.
Review the id_regex_exceptions entries manually before proceeding.
```

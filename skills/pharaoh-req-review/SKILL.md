---
name: pharaoh-req-review
description: Audit a single sphinx-needs requirement against the 10 ISO 26262 Part 8 §6 axes. Emits structured findings JSON — per-axis pass/fail for mechanized axes, 0-3 score for subjective axes, with action items for any failure.
chains_from: [pharaoh-req-draft, pharaoh-req-regenerate]
chains_to: [pharaoh-req-regenerate]
---

# pharaoh-req-review

## When to use

Invoke when the user has a single requirement (either just drafted by `pharaoh-req-draft`, or an
existing need-id present in needs.json) and wants per-axis inspection against ISO 26262-8 §6.

Do NOT review sets of requirements — use `pharaoh-req-set-review` (planned, not in Phase 1).
Do NOT re-author or fix — invoke `pharaoh-req-regenerate` after reviewing.

---

## Inputs

- **target**: either an RST directive block (from `pharaoh-req-draft`) OR a need-id present in
  needs.json
- **tailoring** (from `.pharaoh/project/`):
  - `checklists/requirement.md` — 10 ISO 26262-8 §6 axes
  - `artefact-catalog.yaml` — required/optional fields per artefact type
  - `id-conventions.yaml` — ID regex and prefix map
- **needs.json**: required for link resolution on the verifiability axis

---

## Outputs

A single JSON document with **no prose wrapper**. Shape:

```json
{
  "need_id": "gd_req__example",
  "axes": {
    "atomicity":              {"score": 0, "reason": "..."},
    "internal_consistency":   {"score": 0, "reason": "..."},
    "verifiability":          {"score": 0, "reason": "..."},
    "completeness":           {"score": "deferred", "reason": "set-level axis — see note"},
    "external_consistency":   {"score": "deferred", "reason": "set-level axis — see note"},
    "no_duplication":         {"score": "deferred", "reason": "set-level axis — see note"},
    "schema":                 {"score": 0, "reason": "..."},
    "maintainability":        {"score": null, "reason": "chain-level axis — see note"},
    "unambiguity_prose":      {"score": 0, "reason": "..."},
    "comprehensibility":      {"score": 0, "reason": "..."},
    "feasibility":            {"score": 0, "reason": "..."}
  },
  "action_items": ["..."],
  "overall": "pass"
}
```

### Score scales — two distinct scales, never mixed

**Binary (0 or 1) — mechanized axes** (exec-based scorers define the rule; skill applies the rule
description and records its verdict; the harness compares skill verdict to scorer verdict):

| Axis | Score 0 = FAIL | Score 1 = PASS |
|---|---|---|
| `atomicity` | body contains more than one `shall`, or a coordinating conjunction joins modal verbs within the shall clause | body contains exactly one `shall`; no `, and`/`, or`/` and `/ or ` within the shall clause |
| `internal_consistency` | body contains a self-contradictory statement (e.g. "shall always … unless required not to") | no self-contradiction detectable within this requirement |
| `verifiability` | `:verification:` field absent, empty, or link does not resolve in needs.json | `:verification:` present and resolves to a real need-id in needs.json |
| `schema` | any field listed under `required_fields` in artefact-catalog.yaml is missing from the directive | all required fields present and non-empty |

**Ordinal (0–3) — subjective LLM-judge axes:**

| Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `unambiguity_prose` | multiple conflicting interpretations possible | single interpretation but phrasing is awkward | single interpretation, minor phrasing issues | unambiguous and precise |
| `comprehensibility` | reader at adjacent abstraction level cannot follow | mostly unclear without extra context | mostly clear; minor jargon or ellipsis | fully self-contained and clear |
| `feasibility` | obviously infeasible given item-development constraints | feasible but significant unknowns | feasible with known engineering effort | clearly feasible, well-constrained |

### Deferred set-level axes

`completeness`, `external_consistency`, and `no_duplication` require the full set of sibling
requirements to compute meaningful signal. Scoring them against a single req out of 185 is noise.
These three axes are **deferred to `pharaoh-req-set-review`** (YAGNI in Phase 1).

In the output JSON, record each as `{"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"}`.

### Chain-level axis

`maintainability` (set survives regeneration fixed-point within 2 iterations) cannot be evaluated
at single-requirement or single-invocation scope — it requires running `pharaoh-req-regenerate`
and observing convergence. Record as `{"score": null, "reason": "chain-level axis — assess after pharaoh-req-regenerate runs"}`.

### `overall` field

Computed from the non-deferred, non-null axes only (atomicity, internal_consistency, verifiability,
schema, unambiguity_prose, comprehensibility, feasibility):

- `"pass"` — all binary axes score 1, all subjective axes score ≥ 2
- `"needs_work"` — no binary axis fails, but ≥ 1 subjective axis scores < 2
- `"fail"` — ≥ 1 binary axis scores 0

---

## Process

### Step 1: Read tailoring

Read `.pharaoh/project/checklists/requirement.md`, `.pharaoh/project/artefact-catalog.yaml`, and
`.pharaoh/project/id-conventions.yaml`. Extract:

- Axis definitions (confirm the 10 axes match the expected set)
- `required_fields` for the target artefact type (used in schema axis)
- `id_regex` (used to verify the need-id format if target is an RST block)

If any tailoring file is missing, proceed with Score defaults (gd_req required fields:
`[id, status, satisfies]`). Note the fallback in the output.

### Step 2: Resolve target

**If target is a need-id:**

1. Find needs.json (check `docs/_build/needs/needs.json`, then `_build/needs/needs.json`).
2. Look up the need-id in the needs map.
3. If not found: FAIL immediately (see Guardrails G1).
4. Extract the full directive content: title, all option fields, body text.

**If target is an RST directive block:**

1. Parse the block inline — extract id from `:id:` option, all other options, and body text.
2. Determine artefact type from the directive name (e.g. `.. gd_req::` → type `gd_req`).
3. If needs.json is available, check the id does not already exist (new draft). If it does exist,
   warn but continue — the user may be re-reviewing an existing need.
4. For the verifiability axis, attempt to resolve the `:verification:` link in needs.json.
   If needs.json is not available, record verifiability as `{"score": 0, "reason": "needs.json not available — cannot resolve :verification: link"}`.

### Step 3: Evaluate binary axes

Evaluate each binary axis using the rule from the score-scale table above. Apply the rule textually
to the extracted directive content. Record `score` (0 or 1) and a one-sentence `reason`.

**Atomicity:**
Count occurrences of `shall` in the body text. Check for `, and `, `, or `, ` and `, ` or ` within
the shall clause (from `shall` to end of sentence). Score 1 if exactly one `shall` and no
conjunction; score 0 otherwise.

**Internal consistency:**
Read the body text for contradictory statements (e.g. simultaneous "always" and "unless not
required"). If none detectable, score 1. Score 0 if a self-contradiction is identifiable.

**Verifiability:**
Check whether `:verification:` option is present and non-empty. If present, look up the value as a
need-id in needs.json. Score 1 if present and resolves; score 0 otherwise.

**Schema:**
Check that every field in `required_fields` from artefact-catalog.yaml is present and non-empty in
the directive. For Score `gd_req`: `id`, `status`, `satisfies` must all be present. Score 1 if all
present; score 0 with reason listing the missing field(s).

### Step 4: Evaluate subjective axes

Evaluate using the 0–3 ordinal scale.

**Unambiguity (prose):**
Read the body text. Assess whether a reader could derive more than one meaning from the shall
clause. A single vague term (e.g. "sufficient") is score 1; an unambiguous measurable criterion is
score 3.

**Comprehensibility:**
Assess whether a reader at the adjacent abstraction level (a software architect reading a
component-level req, or a test engineer reading a system-level req) could understand the
requirement without reading any other document. Check for undefined acronyms, missing subject,
and missing context.

**Feasibility:**
Assess whether the requirement as stated could be implemented within typical automotive item
development constraints. Flag physically impossible claims (score 0), heavily under-constrained
targets (score 1), normal engineering effort (score 2), or tightly and clearly bounded
requirements (score 3).

### Step 5: Record deferred and null axes

Set `completeness`, `external_consistency`, `no_duplication` to `{"score": "deferred", ...}` and
`maintainability` to `{"score": null, ...}` per the policy above. Do not attempt to evaluate them.

### Step 6: Compute overall and action items

Compute `overall` from the non-deferred, non-null axes per the rule in the Outputs section.

For each binary axis scoring 0, and each subjective axis scoring 0 or 1, add a concrete action
item to `action_items`. Each action item must name the axis and state what must change.

If all 7 evaluated axes pass/score ≥ 2, `action_items` is an empty array.

### Step 7: Emit JSON

Emit only the JSON document. Do not prepend or append prose.

---

## Guardrails

**G1 — Unresolved target**

If target is a need-id and it does not appear in needs.json:

```
FAIL: need-id "<id>" not found in needs.json.
Verify the ID is correct or build the Sphinx project first (`sphinx-build docs/ docs/_build/`).
```

Do not emit partial JSON. Return only the FAIL message.

**G2 — Malformed JSON output**

If the emitted JSON is syntactically invalid or missing any of the 10 axis keys, self-correct once:
re-emit the full JSON document. If still malformed after one self-correction attempt, emit:

```json
{
  "need_id": "<id>",
  "diagnostic": "JSON self-correction failed. Raw findings follow.",
  "raw": "<free-text findings>"
}
```

**G3 — Insufficient context for subjective axis**

If you cannot meaningfully assess a subjective axis (e.g. body is empty or only a title stub),
record `{"score": 0, "reason": "insufficient context — body is empty or too short to assess"}`.
Do not skip the axis. Continue evaluating the remaining axes.

---

## Advisory chain

If `overall` is `"needs_work"` or `"fail"`, append — after the JSON — a single line:

```
Consider `pharaoh-req-regenerate <need_id>` after addressing action items.
```

This is the only prose permitted after the JSON.

---

## Worked example

**Target (RST block from pharaoh-req-draft):**

```rst
.. gd_req:: ABS pump activation on wheel slip threshold
   :id: gd_req__abs_pump_activation
   :status: draft
   :satisfies: gd_req__brake_system_safety
   :verification: tc__abs_pump_001

   The brake controller shall engage the ABS pump when measured wheel slip exceeds
   the calibrated activation threshold.
```

**Step 2:** RST block parsed. needs.json found; `tc__abs_pump_001` resolves. Parent
`gd_req__brake_system_safety` noted (not evaluated here — verifiability checks `:verification:`).

**Step 3 — binary axes:**
- atomicity: `shall` count = 1; no conjunction in shall clause → score 1
- internal_consistency: no self-contradiction → score 1
- verifiability: `:verification: tc__abs_pump_001` present and resolves → score 1
- schema: `id`, `status`, `satisfies` all present → score 1

**Step 4 — subjective axes:**
- unambiguity_prose: "calibrated activation threshold" is a defined term; single interpretation → score 3
- comprehensibility: subject (brake controller), action (engage ABS pump), condition (wheel slip
  exceeds threshold) all stated; adjacent-level reader can follow → score 3
- feasibility: standard automotive function; well-constrained → score 3

**Step 6:** all 7 evaluated axes pass or score ≥ 2 → `overall = "pass"`, `action_items = []`.

**Step 7 output:**

```json
{
  "need_id": "gd_req__abs_pump_activation",
  "axes": {
    "atomicity":            {"score": 1, "reason": "exactly one shall; no coordinating conjunction in shall clause"},
    "internal_consistency": {"score": 1, "reason": "no self-contradictory statement detected"},
    "verifiability":        {"score": 1, "reason": ":verification: tc__abs_pump_001 resolves in needs.json"},
    "schema":               {"score": 1, "reason": "id, status, satisfies all present"},
    "completeness":         {"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"},
    "external_consistency": {"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"},
    "no_duplication":       {"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"},
    "maintainability":      {"score": null, "reason": "chain-level axis — assess after pharaoh-req-regenerate runs"},
    "unambiguity_prose":    {"score": 3, "reason": "calibrated activation threshold is a defined term; single interpretation"},
    "comprehensibility":    {"score": 3, "reason": "subject, action, and condition all explicit; no undefined acronyms"},
    "feasibility":          {"score": 3, "reason": "standard automotive ABS function; well-constrained threshold trigger"}
  },
  "action_items": [],
  "overall": "pass"
}
```

---

**Variant: two axes fail**

Same requirement but `:verification:` is absent and body reads "The brake controller shall detect
wheel slip and engage the ABS pump when the threshold is exceeded."

Binary axis failures:
- verifiability: `:verification:` absent → score 0
- atomicity: "detect … and engage" — conjunction joins two actions within the shall clause → score 0

```json
{
  "need_id": "gd_req__abs_pump_activation",
  "axes": {
    "atomicity":            {"score": 0, "reason": "conjunction 'and' joins two actions (detect, engage) within the shall clause"},
    "internal_consistency": {"score": 1, "reason": "no self-contradictory statement detected"},
    "verifiability":        {"score": 0, "reason": ":verification: field absent"},
    "schema":               {"score": 1, "reason": "id, status, satisfies all present"},
    "completeness":         {"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"},
    "external_consistency": {"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"},
    "no_duplication":       {"score": "deferred", "reason": "set-level axis — assess with pharaoh-req-set-review"},
    "maintainability":      {"score": null, "reason": "chain-level axis — assess after pharaoh-req-regenerate runs"},
    "unambiguity_prose":    {"score": 2, "reason": "single interpretation but two-action body creates scope ambiguity"},
    "comprehensibility":    {"score": 3, "reason": "subject, action, and condition clear despite atomicity issue"},
    "feasibility":          {"score": 3, "reason": "standard automotive function; well-constrained"}
  },
  "action_items": [
    "atomicity: split into two requirements — one for slip detection, one for ABS pump engagement",
    "verifiability: add :verification: field linking to a test case; use tc__TBD as placeholder before a real test case exists"
  ],
  "overall": "fail"
}
```

Consider `pharaoh-req-regenerate gd_req__abs_pump_activation` after addressing action items.

---
name: pharaoh-vplan-review
description: Use when auditing a single test case against ISO 26262-8 §6 axes plus vplan-specific axes (coverage of parent req, completeness of steps, clarity of expected outcome). Emits structured findings JSON.
chains_from: [pharaoh-vplan-draft]
chains_to: [pharaoh-req-regenerate]
---

# pharaoh-vplan-review

## When to use

Invoke when the user has a single test case (either just drafted by `pharaoh-vplan-draft` or
retrieved from needs.json by ID) and wants per-axis inspection.

Do NOT review sets of test cases — each invocation audits exactly one `tc__` element.
Do NOT re-author or fix — address findings manually or via a planned `pharaoh-vplan-regenerate`
skill, then re-invoke this review.
Do NOT audit requirements or arch elements — use `pharaoh-req-review` or `pharaoh-arch-review`.

---

## Inputs

- **target**: either an RST directive block (from `pharaoh-vplan-draft`) OR a need-id present
  in needs.json
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — `tc` entry; required/optional fields
  - `id-conventions.yaml` — id_regex
- **needs.json**: required for coverage axis (verifying `:verifies:` resolves to parent req) and
  for reading the parent body to check coverage

---

## Outputs

A single JSON document with **no prose wrapper**. Shape mirrors `pharaoh-req-review`, with
`coverage` replacing `verifiability` as the primary traceability axis for test cases:

```json
{
  "need_id": "tc__example",
  "axes": {
    "atomicity":              {"score": 0, "reason": "..."},
    "internal_consistency":   {"score": 0, "reason": "..."},
    "coverage":               {"score": 0, "reason": "..."},
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

Note: `coverage` replaces `verifiability` from req-review. It checks both that the parent link
resolves AND that the test case steps address the testable claim in the parent body.

### Score scales

**Binary (0 or 1) — mechanized axes:**

| Axis | Score 0 = FAIL | Score 1 = PASS |
|---|---|---|
| `atomicity` | test case covers more than one independent testable claim (steps verify two unrelated parent conditions) | test case addresses exactly one testable claim |
| `internal_consistency` | steps or expected outcome contradict each other (e.g. a step asserts X while expected denies X) | no internal contradiction |
| `coverage` | `:verifies:` absent or does not resolve in needs.json, OR the test steps do not address the parent's testable claim | `:verifies:` resolves and test steps address the parent's testable claim |
| `schema` | any field in `required_fields` for the `tc` artefact type is missing | all required fields present and non-empty |

**Ordinal (0–3) — subjective LLM-judge axes:**

| Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `unambiguity_prose` | expected outcome has multiple interpretations or is completely vague ("system works") | single interpretation but phrasing is imprecise | single interpretation; minor imprecision | unambiguous pass/fail criterion |
| `comprehensibility` | test engineer cannot execute this test without reading additional documents | requires significant extra context | mostly self-contained; minor references needed | fully self-contained; executable as-is |
| `feasibility` | test procedure is physically impossible or requires unavailable equipment | feasible but significant setup unknowns | feasible with normal lab equipment | clearly feasible; setup requirements fully specified |

### Deferred set-level axes

`completeness`, `external_consistency`, `no_duplication` require the full set of test cases.
Defer to a planned `pharaoh-vplan-set-review`.

Record each as `{"score": "deferred", "reason": "set-level axis — assess with pharaoh-vplan-set-review"}`.

### Chain-level axis

`maintainability` requires observing regeneration convergence.
Record as `{"score": null, "reason": "chain-level axis — assess after vplan regeneration runs"}`.

### `overall` field

Computed from non-deferred, non-null axes (atomicity, internal_consistency, coverage, schema,
unambiguity_prose, comprehensibility, feasibility):

- `"pass"` — all binary axes score 1, all subjective axes score ≥ 2
- `"needs_work"` — no binary fails, ≥ 1 subjective < 2
- `"fail"` — ≥ 1 binary scores 0

---

## Process

### Step 1: Read tailoring

Read `.pharaoh/project/artefact-catalog.yaml`. Extract the `tc` entry:
- `required_fields` — directive-option keys, expected: `[id, status, verifies]`
- `required_body_sections` — top-level body headings, expected: `[Inputs, Steps, Expected]`

`required_fields` are sphinx-needs directive options (`:id:`, `:status:`, `:verifies:`).
`required_body_sections` are named sections *inside* the directive body prose (`Inputs`,
`Steps`, `Expected`). These are separate axes and validated separately by the `schema` check
below.

If the `tc` entry is absent, apply defaults:
`required_fields = [id, status, verifies]` and
`required_body_sections = [Inputs, Steps, Expected]`. Note the fallback in output.

Read `id-conventions.yaml` for `id_regex`.

---

### Step 2: Resolve target

**If target is a need-id:**

1. Find needs.json (`docs/_build/needs/needs.json` first, then `_build/needs/needs.json`).
2. Look up the need-id. If not found, FAIL (see Guardrails G1).
3. Extract all fields and body (Inputs, Steps, Expected sections).

**If target is an RST directive block:**

1. Parse the block — extract `:id:`, `:status:`, `:verifies:`, `:level:`, and body sections.
2. Identify directive prefix (e.g. `.. tc::` → type `tc`).
3. If needs.json available, check whether the ID already exists.

---

### Step 3: Evaluate binary axes

**Atomicity:**

Read the Steps and Expected sections. Check whether the test case addresses more than one
independent testable claim. Signs of bundled test cases:
- Steps cover two clearly distinct system behaviours (e.g. activation of pump AND logging, with
  no causal relationship between them)
- Expected outcome has two independent pass criteria ("X shall occur AND Y shall occur")

Score 1 if exactly one testable claim is addressed. Score 0 if two or more independent claims
are verified.

**Internal consistency:**

Check for contradictions within the test case:
- A step asserts that a condition is true while the Expected section requires the opposite
- Two steps mutually exclude each other's preconditions

Score 1 if no contradiction; score 0 if one is identifiable.

**Coverage:**

Evaluate two sub-conditions, both must hold for score 1:

*Sub-condition A — link resolution:*
`:verifies:` is present and the ID resolves in needs.json. If absent or unresolved, score 0.

*Sub-condition B — content coverage:*
Read the parent body from needs.json (or from context if target is an RST block and needs.json
is unavailable). Extract the parent's testable claim (the observable outcome or threshold).
Compare against the test Steps and Expected:
- Steps must include an action that stimulates the parent's condition
- Expected must cite the parent's claimed observable

If the test steps and expected do not address the parent's testable claim, score 0 and
describe the gap in `reason`.

Score 1 only if both sub-conditions hold.

**Schema:**

Two independent sub-checks — both must pass to score 1:

1. Every key in `required_fields` is present as a sphinx-needs directive option and
   non-empty. For default tc: `:id:`, `:status:`, `:verifies:` must be set.
2. Every entry in `required_body_sections` is present as a top-level section heading in
   the directive body prose and non-empty. For default tc: `Inputs`, `Steps`, `Expected`
   sections must appear with content.

Score 0 with a `reason` listing the missing fields and/or missing body sections (prefix
option failures with `:field:` and body-section failures with the section name).

---

### Step 4: Evaluate subjective axes

**Unambiguity (prose):**

Read the Expected section. Assess whether a test engineer could judge pass/fail without
interpretation:
- "Pump activates within 50 ms" → score 3
- "Pump activates promptly" → score 1
- "System works correctly" → score 0

**Comprehensibility:**

Assess whether a test engineer could execute this test case end-to-end without reading any
document other than the parent requirement:
- All preconditions in Inputs are explicit
- All steps are unambiguous actions
- No implicit knowledge assumed

**Feasibility:**

Assess whether the test procedure can be executed with normal automotive lab equipment and
environment. Consider:
- Required signals available via CAN/diagnostic interface?
- Fault conditions injectable without destructive testing?
- Timing requirements measurable with standard tools?

---

### Step 5: Record deferred and null axes

Set `completeness`, `external_consistency`, `no_duplication` to deferred.
Set `maintainability` to null. Per policy above.

---

### Step 6: Compute overall and action items

Compute `overall` from non-deferred, non-null axes per the rule above.

For each binary axis scoring 0 and each subjective axis scoring 0 or 1, add a concrete action
item naming the axis and stating what must change.

---

### Step 7: Emit JSON

Emit only the JSON. No prose before or after (except the advisory chain).

---

## Guardrails

**G1 — Unresolved target**

If target is a need-id not found in needs.json:

```
FAIL: need-id "<id>" not found in needs.json.
Verify the ID is correct or build the Sphinx project first.
```

**G2 — Malformed JSON output**

Self-correct once. If still invalid after correction:

```json
{
  "need_id": "<id>",
  "diagnostic": "JSON self-correction failed. Raw findings follow.",
  "raw": "<free-text findings>"
}
```

**G3 — Parent body unavailable for coverage check**

If needs.json is unavailable and target is an RST block, the coverage sub-condition B cannot
be evaluated. Record:

```json
"coverage": {"score": 0, "reason": "parent body unavailable — needs.json not found; link presence checked only"}
```

---

## Advisory chain

If `overall` is `"needs_work"` or `"fail"`, append — after the JSON — a single line:

```
Consider addressing action items and re-running `pharaoh-vplan-review <need_id>`.
```

This is the only prose permitted after the JSON.

---

## Worked example

**Target (RST block from pharaoh-vplan-draft):**

```rst
.. tc:: ABS pump activation on wheel slip threshold — system test
   :id: tc__abs_pump_activation_system
   :status: draft
   :verifies: gd_req__abs_pump_activation
   :level: system

   Inputs:
   - Vehicle moving at 30 km/h on low-friction surface (µ ≤ 0.3)
   - Brake controller in normal operating mode (no active faults)
   - Calibrated wheel slip activation threshold loaded (default factory value)

   Steps:
   1. Apply full brake pedal force to induce wheel lock-up condition.
   2. Monitor measured wheel slip signal via diagnostic interface.
   3. Confirm slip measurement exceeds the calibrated activation threshold.
   4. Observe ABS pump output signal state.

   Expected:
   ABS pump output signal transitions from inactive to active within 50 ms of wheel slip
   measurement exceeding the calibrated activation threshold.
```

**Parent body (from needs.json for `gd_req__abs_pump_activation`):**
> "The brake controller shall engage the ABS pump when measured wheel slip exceeds the
> calibrated activation threshold."

**Step 3 — binary axes:**
- atomicity: one testable claim (pump activation on slip threshold); no second independent claim → score 1
- internal_consistency: steps flow logically; no step contradicts expected outcome → score 1
- coverage: `:verifies: gd_req__abs_pump_activation` resolves; Step 3 stimulates slip threshold
  condition; Expected cites pump activation within 50 ms → score 1
- schema: `id`, `status`, `verifies` present; `inputs` section present; `steps` present;
  `expected` present → score 1

**Step 4 — subjective axes:**
- unambiguity_prose: "transitions from inactive to active within 50 ms" — concrete measurable
  criterion → score 3
- comprehensibility: preconditions, stimuli, and expected outcome fully stated → score 3
- feasibility: slip signal readable via CAN diagnostic interface; 50 ms timing measurable with
  standard tools → score 3

**Step 6:** all 7 evaluated axes pass → `overall = "pass"`, `action_items = []`.

**Step 7 output:**

```json
{
  "need_id": "tc__abs_pump_activation_system",
  "axes": {
    "atomicity":            {"score": 1, "reason": "single testable claim: pump activation on wheel slip threshold"},
    "internal_consistency": {"score": 1, "reason": "no contradiction between steps and expected outcome"},
    "coverage":             {"score": 1, "reason": ":verifies: resolves; steps stimulate slip threshold; expected cites pump activation timing"},
    "schema":               {"score": 1, "reason": "id, status, verifies, inputs, steps, expected all present"},
    "completeness":         {"score": "deferred", "reason": "set-level axis — assess with pharaoh-vplan-set-review"},
    "external_consistency": {"score": "deferred", "reason": "set-level axis — assess with pharaoh-vplan-set-review"},
    "no_duplication":       {"score": "deferred", "reason": "set-level axis — assess with pharaoh-vplan-set-review"},
    "maintainability":      {"score": null, "reason": "chain-level axis — assess after vplan regeneration runs"},
    "unambiguity_prose":    {"score": 3, "reason": "concrete measurable pass criterion: activation within 50 ms"},
    "comprehensibility":    {"score": 3, "reason": "preconditions, stimuli, and expected outcome fully stated"},
    "feasibility":          {"score": 3, "reason": "standard automotive lab setup; slip signal accessible via CAN interface"}
  },
  "action_items": [],
  "overall": "pass"
}
```

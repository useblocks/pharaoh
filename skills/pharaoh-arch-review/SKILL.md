---
name: pharaoh-arch-review
description: Audit a single architecture element against the 10 ISO 26262-8 §6 axes plus arch-specific axes (traceability back to requirement). Emits structured findings JSON.
chains_from: [pharaoh-arch-draft, pharaoh-arch-regenerate]
chains_to: [pharaoh-req-regenerate]
---

# pharaoh-arch-review

## When to use

Invoke when the user has a single architecture element (either just drafted by `pharaoh-arch-draft`
or retrieved from needs.json by ID) and wants per-axis inspection against ISO 26262-8 §6.

Do NOT review sets of arch elements — each invocation audits exactly one element.
Do NOT re-author or fix — invoke `pharaoh-arch-regenerate` (planned) after reviewing if needed.
Do NOT audit requirements — use `pharaoh-req-review` for those.

---

## Inputs

- **target**: either an RST directive block (from `pharaoh-arch-draft`) OR a need-id present
  in needs.json
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — `arch` entry; required/optional fields
  - `id-conventions.yaml` — id_regex and prefix map
- **needs.json**: required for traceability axis (verifying `:satisfies:` resolves to a req)

---

## Outputs

A single JSON document with **no prose wrapper**. Shape mirrors `pharaoh-req-review`, with
`traceability` added as a binary axis and `verifiability` adapted for arch context:

```json
{
  "need_id": "arch__example",
  "axes": {
    "atomicity":              {"score": 0, "reason": "..."},
    "internal_consistency":   {"score": 0, "reason": "..."},
    "traceability":           {"score": 0, "reason": "..."},
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

Note: `verifiability` from req-review is replaced by `traceability` for arch elements. Architecture
elements are not directly tested; they must *trace* to a requirement that carries the verification
link.

### Score scales

**Binary (0 or 1) — mechanized axes:**

| Axis | Score 0 = FAIL | Score 1 = PASS |
|---|---|---|
| `atomicity` | element bundles more than one distinct architectural concern (e.g. two independent responsibilities in the body) | element represents exactly one coherent architectural unit |
| `internal_consistency` | body contains a self-contradictory statement | no self-contradiction detectable within this element |
| `traceability` | `:satisfies:` field absent, empty, or the linked ID does not exist in needs.json as a requirement type | `:satisfies:` present and resolves to a requirement-type need in needs.json |
| `schema` | any field listed in `required_fields` for the `arch` entry in artefact-catalog.yaml is missing | all required fields present and non-empty |

**Ordinal (0–3) — subjective LLM-judge axes:**

| Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `unambiguity_prose` | multiple conflicting interpretations of the element's responsibility | single interpretation but phrasing is awkward | single clear interpretation; minor phrasing issues | unambiguous and precise |
| `comprehensibility` | adjacent-level reader (test engineer or architect) cannot follow | mostly unclear without extra context | mostly clear; minor jargon | fully self-contained and clear |
| `feasibility` | obviously unrealisable given item-development constraints | realisable but significant unknowns | realisable with known engineering effort | clearly realisable; well-bounded |

### Deferred set-level axes

`completeness`, `external_consistency`, and `no_duplication` require the full set of sibling
architecture elements. Defer to a planned `pharaoh-arch-set-review` skill.

In the output JSON, record each as
`{"score": "deferred", "reason": "set-level axis — assess with pharaoh-arch-set-review"}`.

### Chain-level axis

`maintainability` requires observing convergence across regeneration iterations. Record as
`{"score": null, "reason": "chain-level axis — assess after pharaoh-arch-regenerate runs"}`.

### `overall` field

Computed from non-deferred, non-null axes (atomicity, internal_consistency, traceability, schema,
unambiguity_prose, comprehensibility, feasibility):

- `"pass"` — all binary axes score 1, all subjective axes score ≥ 2
- `"needs_work"` — no binary axis fails, but ≥ 1 subjective axis scores < 2
- `"fail"` — ≥ 1 binary axis scores 0

---

## Process

### Step 1: Read tailoring

Read `.pharaoh/project/artefact-catalog.yaml` and `.pharaoh/project/id-conventions.yaml`.

For the `arch` artefact type, extract:
- `required_fields` (expected: `[id, status, satisfies, type]`)
- `id_regex`

If the `arch` entry is absent from artefact-catalog, apply defaults:
- `required_fields`: `[id, status, satisfies, type]`
Note the fallback in output.

---

### Step 2: Resolve target

**If target is a need-id:**

1. Find needs.json (`docs/_build/needs/needs.json`, then `_build/needs/needs.json`).
2. Look up the need-id in the needs map.
3. If not found, FAIL (see Guardrails G1).
4. Extract title, all option fields, and body text.

**If target is an RST directive block:**

1. Parse the block — extract `:id:`, `:status:`, `:satisfies:`, `:type:`, and body.
2. Determine artefact type from the directive name (e.g. `.. arch::` → type `arch`).
3. If needs.json is available, check whether the ID already exists (may be a re-review).

---

### Step 3: Evaluate binary axes

**Atomicity:**

Read the body. Assess whether it describes a single coherent architectural concern or bundles
multiple independent responsibilities. Look for:
- Multiple distinct systems or subsystems described as owned by this element
- Compound responsibility lists joined by "and" describing unrelated concerns

Score 1 if the body describes one coherent unit. Score 0 if two or more clearly separable
responsibilities are described.

**Internal consistency:**

Read the body for contradictory statements (e.g. "is responsible for X" followed by "does not
handle X"). Score 1 if no contradiction; score 0 if one is identifiable.

**Traceability:**

Check `:satisfies:` option:
1. Present and non-empty — if absent, score 0.
2. Resolves in needs.json — if the ID does not exist, score 0.
3. The resolved need is a requirement type (prefix ends in `req` or equivalent) — if it is a
   non-requirement type (e.g. `wf`, `wp`), score 0 and note the type mismatch.

Score 1 only if all three conditions hold.

**Schema:**

Verify every field in `required_fields` is present and non-empty. For default arch:
`id`, `status`, `satisfies`, `type` must all be present. Score 0 with reason listing missing
field(s) if any are absent.

---

### Step 4: Evaluate subjective axes

**Unambiguity (prose):**

Read the body. Assess whether a reader can derive only one interpretation of the element's
responsibility. Vague ownership ("may handle", "is sometimes responsible for") → score 1.
Clear, bounded description → score 3.

**Comprehensibility:**

Assess whether a test engineer or software architect at an adjacent level could understand what
this element does without reading any other document. Check for undefined acronyms, missing
subject, and missing context. Full clarity → score 3; requires significant additional context →
score 0.

**Feasibility:**

Assess whether the element as described could be realised within typical automotive software
item-development constraints. Flag obviously infeasible claims (score 0), heavily under-constrained
elements (score 1), normal engineering effort (score 2), or tightly and clearly bounded elements
(score 3).

---

### Step 5: Record deferred and null axes

Set `completeness`, `external_consistency`, `no_duplication` to
`{"score": "deferred", "reason": "set-level axis — assess with pharaoh-arch-set-review"}` and
`maintainability` to
`{"score": null, "reason": "chain-level axis — assess after pharaoh-arch-regenerate runs"}`.

---

### Step 6: Compute overall and action items

Compute `overall` from non-deferred, non-null axes per the policy above.

For each binary axis scoring 0 and each subjective axis scoring 0 or 1, add a concrete action
item naming the axis and stating what must change.

If all 7 evaluated axes pass/score ≥ 2, `action_items` is an empty array.

---

### Step 7: Emit JSON

Emit only the JSON document. Do not prepend or append prose.

---

## Guardrails

**G1 — Unresolved target**

If target is a need-id and it does not appear in needs.json:

```
FAIL: need-id "<id>" not found in needs.json.
Verify the ID is correct or build the Sphinx project first.
```

**G2 — Malformed JSON output**

If the emitted JSON is syntactically invalid or missing any axis key, self-correct once. If still
malformed after one correction attempt:

```json
{
  "need_id": "<id>",
  "diagnostic": "JSON self-correction failed. Raw findings follow.",
  "raw": "<free-text findings>"
}
```

**G3 — Insufficient context for subjective axis**

If the element body is empty or too short to assess a subjective axis, record:
`{"score": 0, "reason": "insufficient context — body is empty or too short to assess"}`.
Continue evaluating remaining axes.

---

## Advisory chain

If `overall` is `"needs_work"` or `"fail"`, append — after the JSON — a single line:

```
Consider `pharaoh-arch-regenerate <need_id>` after addressing action items.
```

This is the only prose permitted after the JSON.

---

## Worked example

**Target (RST block from pharaoh-arch-draft):**

```rst
.. arch:: ABS pump driver component
   :id: arch__abs_pump_driver
   :status: draft
   :satisfies: gd_req__abs_pump_activation
   :type: component

   The ABS pump driver component manages the pump drive circuit, controlling output
   PWM duty cycle and providing over-current protection for the pump motor.
```

**Step 2:** RST parsed. needs.json found; `gd_req__abs_pump_activation` resolves as type `gd_req`.

**Step 3 — binary axes:**
- atomicity: body describes one coherent unit (pump drive circuit management); no separate
  unrelated concerns → score 1
- internal_consistency: no self-contradiction → score 1
- traceability: `:satisfies: gd_req__abs_pump_activation` present; resolves in needs.json;
  type is `gd_req` → score 1
- schema: `id`, `status`, `satisfies`, `type` all present → score 1

**Step 4 — subjective axes:**
- unambiguity_prose: single clear interpretation (manages pump drive circuit) → score 3
- comprehensibility: subject, responsibility, and constraints explicit; no undefined acronyms
  (PWM is standard automotive abbreviation) → score 3
- feasibility: standard automotive power electronics function; well-constrained → score 3

**Step 6:** all 7 evaluated axes pass or score ≥ 2 → `overall = "pass"`, `action_items = []`.

**Step 7 output:**

```json
{
  "need_id": "arch__abs_pump_driver",
  "axes": {
    "atomicity":            {"score": 1, "reason": "single coherent unit: pump drive circuit management"},
    "internal_consistency": {"score": 1, "reason": "no self-contradictory statement detected"},
    "traceability":         {"score": 1, "reason": ":satisfies: gd_req__abs_pump_activation resolves as type gd_req"},
    "schema":               {"score": 1, "reason": "id, status, satisfies, type all present"},
    "completeness":         {"score": "deferred", "reason": "set-level axis — assess with pharaoh-arch-set-review"},
    "external_consistency": {"score": "deferred", "reason": "set-level axis — assess with pharaoh-arch-set-review"},
    "no_duplication":       {"score": "deferred", "reason": "set-level axis — assess with pharaoh-arch-set-review"},
    "maintainability":      {"score": null, "reason": "chain-level axis — assess after pharaoh-arch-regenerate runs"},
    "unambiguity_prose":    {"score": 3, "reason": "single clear interpretation: manages pump drive circuit"},
    "comprehensibility":    {"score": 3, "reason": "subject, responsibility, and constraints all explicit"},
    "feasibility":          {"score": 3, "reason": "standard automotive power electronics function; well-constrained"}
  },
  "action_items": [],
  "overall": "pass"
}
```

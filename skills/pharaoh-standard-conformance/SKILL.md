---
name: pharaoh-standard-conformance
description: Evaluate a single sphinx-needs artefact against one regulatory standard (ISO 26262-8 §6, ASPICE 4.0, ISO/SAE 21434). Emits per-indicator findings JSON with pass/fail on mechanizable indicators and 0-3 scores on subjective ones.
chains_from: [pharaoh-req-review, pharaoh-arch-review, pharaoh-vplan-review, pharaoh-process-audit]
chains_to: []
---

# pharaoh-standard-conformance

## When to use

Invoke when you want to check whether a single artefact (requirement, architecture element, or
verification plan) meets the mandatory indicators of one named regulatory standard.

**One artefact, one standard per invocation.** For a full corpus audit across multiple artefacts
and gap categories, invoke `pharaoh-process-audit` instead.

Do NOT use to author or fix the artefact — run the relevant `*-review` skill for quality
feedback, then `pharaoh-req-regenerate` or re-draft to address findings.

---

## Inputs

- **artefact**: either an RST directive block (inline) or a need-id present in `needs.json`
- **standard**: one of `iso26262` | `aspice40` | `iso21434`
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — required/optional fields per artefact type
  - `id-conventions.yaml` — ID regex and prefix map
- **needs.json**: required for link resolution (field references to other needs)

---

## Outputs

A single JSON document — no prose wrapper. Top-level shape:

```json
{
  "standard": "iso26262",
  "artefact_id": "gd_req__example",
  "artefact_type": "gd_req",
  "indicators": [
    {
      "id": "SC-ISO-01",
      "name": "schema_completeness",
      "type": "mechanized",
      "result": 1,
      "evidence": "All required fields (id, status, satisfies) present."
    }
  ],
  "overall": "pass"
}
```

### `indicators` array

Each entry:

| Field | Type | Description |
|---|---|---|
| `id` | string | Indicator identifier, e.g. `SC-ISO-01` |
| `name` | string | Short snake_case name |
| `type` | `"mechanized"` or `"subjective"` | Determines result scale |
| `result` | integer | `0` or `1` for mechanized; `0–3` for subjective |
| `evidence` | string | One-sentence justification |

### `overall` field

Derived from all indicators:

- `"pass"` — all mechanized indicators score 1, all subjective score ≥ 2
- `"partial"` — no mechanized indicator scores 0, but ≥ 1 subjective indicator scores < 2
- `"fail"` — ≥ 1 mechanized indicator scores 0

---

## Indicator sets per standard

### ISO 26262-8 §6 (standard: `iso26262`)

Cross-references the 10 ISO axes from `pharaoh-req-review` — this skill applies the same axes
but maps them to ISO 26262 Part 8 §6 indicator language.

| ID | Name | Type | Pass rule |
|---|---|---|---|
| SC-ISO-01 | schema_completeness | mechanized | All `required_fields` from artefact-catalog.yaml are present and non-empty |
| SC-ISO-02 | unique_identification | mechanized | `id` matches `id_regex` from id-conventions.yaml for this artefact type |
| SC-ISO-03 | verifiability | mechanized | `:verification:` (for req) or `:verifies:` (for tc) present and resolves in needs.json |
| SC-ISO-04 | traceability_upward | mechanized | `:satisfies:` or `:verifies:` link present and resolves to a parent in needs.json |
| SC-ISO-05 | atomicity | mechanized | Body contains exactly one `shall`; no coordinating conjunction joins actions within the shall clause |
| SC-ISO-06 | unambiguity | subjective | 0–3 scale: 3 = measurable and unambiguous; 0 = multiple valid interpretations |
| SC-ISO-07 | comprehensibility | subjective | 0–3 scale: 3 = self-contained, no undefined terms; 0 = requires external context to interpret |
| SC-ISO-08 | feasibility | subjective | 0–3 scale: 3 = clearly achievable within known engineering constraints; 0 = infeasible or contradictory |

For non-requirement artefacts (arch, tc): SC-ISO-05 atomicity is recorded as `{"result": null,
"evidence": "atomicity indicator applies to requirements only"}`.

### ASPICE 4.0 (standard: `aspice40`)

| ID | Name | Type | Pass rule |
|---|---|---|---|
| SC-APC-01 | sup10_traceability | mechanized | Every requirement has a bi-directional link: upward (`:satisfies:`) and downward (`:verification:` or linked tc `:verifies:`); both must resolve in needs.json |
| SC-APC-02 | swe1_elicitation_completeness | mechanized | Artefact carries `status` field with a value declared in workflows.yaml lifecycle_states |
| SC-APC-03 | swe2_design_linkage | mechanized | For arch artefacts: `:satisfies:` resolves to a gd_req in needs.json. For non-arch artefacts: recorded as `null` (not applicable) |
| SC-APC-04 | sup8_config_id | mechanized | `id` matches id-conventions.yaml id_regex for its type |
| SC-APC-05 | swe1_rationale_quality | subjective | 0–3: 3 = stakeholder intent and justification explicitly stated; 0 = no rationale whatsoever |
| SC-APC-06 | swe2_design_adequacy | subjective | 0–3: 3 = design element clearly addresses the stated requirement; 0 = no discernible connection |

### ISO/SAE 21434 (standard: `iso21434`)

| ID | Name | Type | Pass rule |
|---|---|---|---|
| SC-CS-01 | cs_rm01_risk_management | mechanized | Artefact references a TARA or threat ID in a `complies` or `tags` field (value matches regex `tara__.*` or `threat__.*`) |
| SC-CS-02 | cs_traceability | mechanized | Upward link (`:satisfies:`) present and resolves; for tc: `:verifies:` present and resolves |
| SC-CS-03 | cs_unique_id | mechanized | `id` matches id-conventions.yaml id_regex |
| SC-CS-04 | cs_threat_analysis_adequacy | subjective | 0–3: 3 = cyber threat scenario described with attack vector, impact, and likelihood; 0 = no threat context mentioned |
| SC-CS-05 | cs_risk_treatment_rationale | subjective | 0–3: 3 = chosen risk treatment (accept/mitigate/avoid/transfer) stated with explicit justification; 0 = treatment absent |

---

## Process

### Step 1: Validate inputs

Confirm `artefact` and `standard` are provided. If `standard` is not one of `iso26262`,
`aspice40`, `iso21434`, FAIL immediately:

```
FAIL: unknown standard "<value>".
Supported standards: iso26262, aspice40, iso21434.
```

If `artefact` is absent, FAIL:

```
FAIL: no artefact provided.
Supply either a need-id or an RST directive block.
```

---

### Step 2: Read tailoring

Read `.pharaoh/project/artefact-catalog.yaml` and `.pharaoh/project/id-conventions.yaml`.
Extract `required_fields` for the artefact type and `id_regex` for the type prefix.

If tailoring files are missing, apply Score defaults:
- `gd_req` required fields: `[id, status, satisfies]`
- `arch` required fields: `[id, status, satisfies, type]`
- `tc` required fields: `[id, status, verifies]`

Note the fallback in each affected indicator's `evidence`.

---

### Step 3: Resolve artefact

**If artefact is a need-id:** Look up in needs.json. If not found, FAIL (G1).
Extract all fields and body text.

**If artefact is an RST block:** Parse inline — extract id from `:id:` option, all other
options, and body text. Determine type from the directive name (e.g. `.. gd_req::` → `gd_req`).
For link-resolution indicators, use needs.json if available; record
`"needs.json unavailable — link unresolvable"` in evidence and score 0 if not.

---

### Step 4: Evaluate indicators

Apply the indicator set for the selected `standard` (see tables above).

For each **mechanized** indicator:
- Apply the stated pass rule deterministically.
- Record `result: 1` (pass) or `result: 0` (fail) and one-sentence `evidence`.

For each **subjective** indicator:
- Apply the 0–3 scale description.
- Record integer score and one-sentence `evidence`.

For not-applicable indicators (e.g. SC-ISO-05 atomicity on an arch artefact), record
`result: null` with a brief `evidence` string. Null indicators do not affect `overall`.

---

### Step 5: Compute overall

Inspect all non-null indicators:
- Any mechanized `result: 0` → `overall: "fail"`
- No mechanized failures but any subjective `result < 2` → `overall: "partial"`
- All mechanized `result: 1` and all subjective `result ≥ 2` → `overall: "pass"`

---

### Step 6: Emit JSON

Emit the single JSON document. No prose before or after.

---

## Guardrails

**G1 — Artefact not found**

If artefact is a need-id and it does not appear in needs.json:

```
FAIL: need-id "<id>" not found in needs.json.
Verify the ID or rebuild the project first (sphinx-build docs/ docs/_build/).
```

Do not emit partial JSON.

**G2 — Unknown standard**

Unknown `standard` value → FAIL (Step 1) with list of supported standards. Do not attempt
indicator evaluation.

**G3 — Unparseable RST block**

If the provided RST block cannot be parsed (no `.. <type>::` opener, no `:id:` option):

```
FAIL: cannot parse artefact RST block.
Expected format: ".. <type>:: <title>" followed by indented :id: option.
Check indentation and directive syntax.
```

**G4 — Malformed JSON self-correction**

If emitted JSON is syntactically invalid, self-correct once. On second failure:

```json
{
  "standard": "<standard>",
  "artefact_id": "<id>",
  "diagnostic": "JSON self-correction failed. Raw findings follow.",
  "raw": "<free-text findings>"
}
```

---

## Advisory chain

`chains_to: []` — this skill is terminal. If `overall` is `"partial"` or `"fail"`, append a
single advisory line after the JSON:

For `iso26262` findings: suggest `pharaoh-req-review` for detailed axis-level action items.
For `aspice40` / `iso21434` findings: suggest re-authoring the artefact to address failing
indicators directly.

---

## Worked example

### Run 1: ISO 26262 on a `gd_req`

**Input:**
- `standard`: `iso26262`
- `artefact` (RST block):

```rst
.. gd_req:: ABS pump activation on wheel slip threshold
   :id: gd_req__abs_pump_activation
   :status: draft
   :satisfies: gd_req__brake_system_safety
   :verification: tc__abs_pump_001

   The brake controller shall engage the ABS pump when measured wheel slip
   exceeds the calibrated activation threshold.
```

**Step 1:** standard `iso26262` valid; artefact provided.

**Step 2:** tailoring loaded; `gd_req` required fields: `[id, status, satisfies]`.

**Step 3:** RST parsed. `id = gd_req__abs_pump_activation`, `type = gd_req`.
needs.json available; `tc__abs_pump_001` and `gd_req__brake_system_safety` both resolve.

**Step 4 — mechanized indicators:**
- SC-ISO-01: `id`, `status`, `satisfies` all present → result 1
- SC-ISO-02: `gd_req__abs_pump_activation` matches `gd_req__[a-z0-9_]+` → result 1
- SC-ISO-03: `:verification: tc__abs_pump_001` resolves → result 1
- SC-ISO-04: `:satisfies: gd_req__brake_system_safety` resolves → result 1
- SC-ISO-05: one `shall`, no coordinating conjunction → result 1

**Step 4 — subjective indicators:**
- SC-ISO-06: "calibrated activation threshold" is a defined term; single interpretation → score 3
- SC-ISO-07: subject/action/condition all explicit; no undefined acronyms → score 3
- SC-ISO-08: standard automotive ABS function; well-constrained → score 3

**Step 5:** all mechanized pass, all subjective ≥ 2 → `overall: "pass"`.

```json
{
  "standard": "iso26262",
  "artefact_id": "gd_req__abs_pump_activation",
  "artefact_type": "gd_req",
  "indicators": [
    {"id": "SC-ISO-01", "name": "schema_completeness",  "type": "mechanized", "result": 1, "evidence": "id, status, satisfies all present and non-empty"},
    {"id": "SC-ISO-02", "name": "unique_identification", "type": "mechanized", "result": 1, "evidence": "gd_req__abs_pump_activation matches gd_req__[a-z0-9_]+ regex"},
    {"id": "SC-ISO-03", "name": "verifiability",         "type": "mechanized", "result": 1, "evidence": ":verification: tc__abs_pump_001 resolves in needs.json"},
    {"id": "SC-ISO-04", "name": "traceability_upward",   "type": "mechanized", "result": 1, "evidence": ":satisfies: gd_req__brake_system_safety resolves in needs.json"},
    {"id": "SC-ISO-05", "name": "atomicity",             "type": "mechanized", "result": 1, "evidence": "exactly one shall; no coordinating conjunction in shall clause"},
    {"id": "SC-ISO-06", "name": "unambiguity",           "type": "subjective", "result": 3, "evidence": "calibrated activation threshold is a defined term; single interpretation"},
    {"id": "SC-ISO-07", "name": "comprehensibility",     "type": "subjective", "result": 3, "evidence": "subject, action, and condition explicit; no undefined acronyms"},
    {"id": "SC-ISO-08", "name": "feasibility",           "type": "subjective", "result": 3, "evidence": "standard automotive ABS function; well-constrained threshold trigger"}
  ],
  "overall": "pass"
}
```

---

### Run 2: ASPICE 4.0 on the same `gd_req`

Same artefact as Run 1. Standard changed to `aspice40` — different indicator set, same artefact.

**Step 4 — mechanized indicators:**
- SC-APC-01: `:satisfies:` resolves upward AND `:verification: tc__abs_pump_001` resolves
  downward → SUP.10 traceability satisfied → result 1
- SC-APC-02: `status: draft` is declared in workflows.yaml lifecycle_states → result 1
- SC-APC-03: `gd_req` is not an arch artefact → result null (not applicable)
- SC-APC-04: id matches regex → result 1

**Step 4 — subjective indicators:**
- SC-APC-05: no `rationale:` field present; stakeholder intent not stated → score 1
- SC-APC-06: not applicable to req type → result null

**Step 5:** SC-APC-01, -02, -04 pass; SC-APC-03 and SC-APC-06 null; SC-APC-05 scores 1 (< 2) →
`overall: "partial"`.

```json
{
  "standard": "aspice40",
  "artefact_id": "gd_req__abs_pump_activation",
  "artefact_type": "gd_req",
  "indicators": [
    {"id": "SC-APC-01", "name": "sup10_traceability",           "type": "mechanized", "result": 1,    "evidence": "upward :satisfies: and downward :verification: both resolve"},
    {"id": "SC-APC-02", "name": "swe1_elicitation_completeness","type": "mechanized", "result": 1,    "evidence": "status 'draft' declared in workflows.yaml lifecycle_states"},
    {"id": "SC-APC-03", "name": "swe2_design_linkage",          "type": "mechanized", "result": null, "evidence": "not applicable to gd_req artefact type"},
    {"id": "SC-APC-04", "name": "sup8_config_id",               "type": "mechanized", "result": 1,    "evidence": "id matches id_regex for gd_req prefix"},
    {"id": "SC-APC-05", "name": "swe1_rationale_quality",       "type": "subjective", "result": 1,    "evidence": "no :rationale: field; stakeholder intent not explicitly stated"},
    {"id": "SC-APC-06", "name": "swe2_design_adequacy",         "type": "subjective", "result": null, "evidence": "not applicable to gd_req artefact type"}
  ],
  "overall": "partial"
}
```

Consider re-authoring the artefact to add a `:rationale:` field addressing SC-APC-05.

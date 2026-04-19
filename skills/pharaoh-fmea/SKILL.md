---
name: pharaoh-fmea
description: Derive a single failure-mode entry (FMEA / DFA row) from one requirement or architecture element. Emits structured JSON with cause, effect, severity (1-10), occurrence (1-10), detection (1-10), and RPN.
chains_from: [pharaoh-req-draft, pharaoh-arch-draft]
chains_to: []
---

# pharaoh-fmea

## When to use

Invoke when the user has a requirement or architecture element and wants to derive one failure-mode
entry from it. Each invocation produces exactly one FMEA row.

Do NOT derive multiple failure modes in one invocation — one mode per call. If the parent element
implies several potential failure modes, derive the most safety-critical one and advise the user
to re-invoke for others.
Do NOT produce RST output — FMEA entries are tabular/JSON artefacts, not sphinx-needs directives.
Do NOT score whole systems — one failure mode, one parent element per call.

---

## Inputs

- **parent_id** (from user): need-id of the parent requirement or architecture element
  — must exist in needs.json
- **failure_mode** (from user): short description of the specific failure to analyse
  (optional — if omitted, derive the most apparent failure mode from the parent body)
- **safety_context** (from user, optional): ASIL level (A–D) or safety goal if known; informs
  severity rating
- **needs.json**: required for parent resolution

---

## Outputs

A single JSON object — no RST, no prose wrapper:

```json
{
  "fmea_id": "fmea__<parent_local_id>__<mode>",
  "parent": "<parent_id>",
  "failure_mode": "short description of how the element fails",
  "cause": "root cause or failure mechanism",
  "effect": "downstream consequence if failure is not detected",
  "severity": 1,
  "occurrence": 1,
  "detection": 1,
  "rpn": 1,
  "mitigations": ["mitigation or design control"],
  "justifications": {
    "severity": "one-sentence rationale for the severity score",
    "occurrence": "one-sentence rationale for the occurrence score",
    "detection": "one-sentence rationale for the detection score"
  }
}
```

`rpn` is always `severity × occurrence × detection`. Do not emit a pre-computed value that
differs from this product.

---

## Rating scales

All three ordinal dimensions use 1–10 per AIAG-VDA FMEA / ISO 26262 severity-risk convention:

### Severity (S) — consequence of the failure effect

| Score | Meaning |
|---|---|
| 9–10 | Hazardous: safety-critical failure; may result in injury or loss of life; ASIL C/D item |
| 7–8 | High: significant damage or non-compliance; ASIL B item |
| 5–6 | Moderate: degraded function; customer/operator dissatisfied; ASIL A item |
| 3–4 | Low: minor degraded function; slight annoyance |
| 1–2 | None to negligible: no discernible effect |

### Occurrence (O) — likelihood of the cause occurring

| Score | Meaning |
|---|---|
| 9–10 | Very high: failure is almost certain (≥ 1 in 100 operations) |
| 7–8 | High: repeated failures (≥ 1 in 1000 operations) |
| 5–6 | Moderate: occasional failures (≥ 1 in 10 000 operations) |
| 3–4 | Low: relatively few failures |
| 1–2 | Remote: failure is unlikely |

### Detection (D) — likelihood that the failure is NOT detected before reaching the customer / next level

| Score | Meaning |
|---|---|
| 9–10 | Almost impossible to detect; no control mechanism in place |
| 7–8 | Very low chance of detection |
| 5–6 | Moderate detection probability |
| 3–4 | High detection probability; test or monitoring in place |
| 1–2 | Almost certain detection; continuous monitoring or mandatory test |

> LLM-judge is the source of truth for scoring. Scores reflect the LLM's reasoning from the
> parent element body and safety_context. Harness spot-checks against human-rated samples.

---

## Process

### Step 1: Locate and parse needs.json

Find `needs.json` (check `docs/_build/needs/needs.json`, then `_build/needs/needs.json`, then
any `needs.json` under a `_build` directory). If not found, FAIL:

```
FAIL: needs.json not found. Build the Sphinx project first (`sphinx-build docs/ docs/_build/`),
then re-run this skill.
```

Extract a flat map of `id → {id, type, status, body}`.

---

### Step 2: Validate parent_id

Look up `parent_id` in the needs.json map. If not found, FAIL:

```
FAIL: parent_id "<id>" not found in needs.json.
Specify an existing requirement or architecture element ID.
```

Extract the parent body — this is the primary source for deriving failure mode, cause, and effect.

---

### Step 3: Determine failure_mode

If `failure_mode` was provided by the user, use it as-is (cleaned to ≤ 8 words, lowercase with
underscores for the ID slug).

If `failure_mode` was not provided:
1. Read the parent body.
2. Identify the primary function or constraint being specified.
3. Derive the most apparent failure mode: "What happens if this function does NOT occur, occurs
   incorrectly, or occurs at the wrong time?"
4. State the failure mode as a short noun phrase: e.g. "no ABS pump activation on wheel slip".

If the parent body is too vague to derive a failure mode, FAIL:

```
FAIL: parent "<parent_id>" body is too vague to derive a failure mode.
Provide explicit failure_mode in the input or improve the parent element first.
```

---

### Step 4: Derive cause, effect, and mitigations

**Cause:** Root cause or failure mechanism at the element level. Focus on the element itself:
hardware fault, software logic error, interface signal loss, incorrect parameterisation, etc.
One concrete cause per FMEA entry.

**Effect:** Downstream consequence if this failure propagates undetected. Describe the effect
at the system / vehicle / user level (not just at the element level). Reference the parent's
role in the safety chain.

**Mitigations:** One to three design controls or mitigations that reduce severity, occurrence,
or detection probability. Examples: watchdog monitoring, redundant sensor path, end-of-line
calibration test, periodic self-test.

If safety_context (ASIL level) was provided, reference it in the effect and severity
justification.

---

### Step 5: Assign S / O / D scores and compute RPN

For each dimension, select a score from the 1–10 scale using the tables above and the parent
body plus safety_context. Write a one-sentence justification per dimension.

**Severity:** driven primarily by the effect description and ASIL level if known.

**Occurrence:** driven by the failure mechanism type (random hardware fault vs. systematic
software defect) and any field-experience hints in the parent body or safety_context.

**Detection:** driven by what monitoring or testing is stated or implied in the parent element.
If the parent has a `:verification:` link, lower detection score (better detection). If no
verification is present, default to score 7 (poor detection assumed).

Compute: `rpn = severity × occurrence × detection`.

---

### Step 6: Assign fmea_id

Format: `fmea__<parent_local>__<mode_slug>`

Where:
- `parent_local` is the local part of parent_id (after the separator `__`)
- `mode_slug` is the failure_mode short form: lowercase, underscores, ≤ 5 words

Example: parent `gd_req__abs_pump_activation`, mode "no activation on slip" →
`fmea__abs_pump_activation__no_activation`.

---

### Step 7: Self-check

Before emitting:

- `rpn` == `severity × occurrence × detection` (recompute and verify)
- All three scores are integers in 1–10
- All three justification strings are non-empty
- `fmea_id` matches the `fmea__<parent_local>__<mode_slug>` format
- `mitigations` contains at least one item

If any check fails, correct and re-check once. If still failing, emit with `[DIAGNOSTIC]`.

---

### Step 8: Emit JSON

Emit the single JSON object. No prose before or after except the advisory note.

If multiple failure modes were apparent from the parent element and only one is emitted, append
after the JSON:

```
[NOTE] Additional failure modes may be apparent from this element.
Re-invoke pharaoh-fmea with an explicit failure_mode argument for each additional mode.
```

---

## Guardrails

**G1 — Parent not found**

parent_id absent from needs.json → FAIL (Step 2).

**G2 — Parent body too vague**

No derivable failure mode → FAIL (Step 3). Do not invent a generic placeholder failure mode.

**G3 — Multiple failure modes inferred**

If the parent implies more than one distinct failure mode, derive the highest-severity one and
emit the `[NOTE]` advisory (Step 8). Do not bundle two failure modes in one JSON entry.

**G4 — needs.json unavailable**

Cannot find needs.json → FAIL (Step 1).

**G5 — RPN mismatch**

If the emitted `rpn` field does not equal `severity × occurrence × detection`, self-correct
before emitting. Never emit a mismatched RPN.

---

## Advisory chain

This skill has no downstream chain (`chains_to: []`). No advisory is appended unless multiple
failure modes were detected (see Step 8 `[NOTE]`).

---

## Worked example

**User input:**
> Parent: `gd_req__abs_pump_activation`; no explicit failure_mode; safety_context: ASIL B.

**Parent body (from needs.json):**
> "The brake controller shall engage the ABS pump when measured wheel slip exceeds the
> calibrated activation threshold."

**Step 3 — derive failure_mode:**
Primary function: engage ABS pump on slip threshold exceedance.
Most apparent failure: pump is not engaged despite slip threshold being exceeded.
failure_mode = "no ABS pump activation on slip threshold exceedance"

**Step 4:**
- cause: "Brake controller software fails to detect slip threshold exceedance due to ADC input
  signal corruption or watchdog reset during the slip-detection window."
- effect: "ABS pump does not activate; wheel locks up during emergency braking; braking distance
  increases; driver loses directional control. ASIL B safety goal potentially violated."
- mitigations: ["Watchdog monitoring on slip-detection task", "Redundant wheel speed sensor
  input path", "End-of-line ABS activation test before vehicle delivery"]

**Step 5 — S/O/D:**
- severity = 8; justification: "Failure to activate ABS during emergency braking can cause loss
  of directional control, significant injury risk — ASIL B item."
- occurrence = 4; justification: "ADC signal corruption or watchdog reset is a low-probability
  systematic defect in a mature ECU design."
- detection = 5; justification: "No continuous runtime monitoring of pump-activation response
  is stated in the parent requirement; EoL test improves detection but does not eliminate
  in-field risk."
- rpn = 8 × 4 × 5 = 160

**Step 6:** fmea_id = `fmea__abs_pump_activation__no_activation`

**Step 7:** rpn == 160; all scores 1–10; justifications non-empty; at least one mitigation. Pass.

**Step 8 output:**

```json
{
  "fmea_id": "fmea__abs_pump_activation__no_activation",
  "parent": "gd_req__abs_pump_activation",
  "failure_mode": "no ABS pump activation on slip threshold exceedance",
  "cause": "Brake controller software fails to detect slip threshold exceedance due to ADC input signal corruption or watchdog reset during the slip-detection window.",
  "effect": "ABS pump does not activate; wheel locks up during emergency braking; braking distance increases; driver loses directional control. ASIL B safety goal potentially violated.",
  "severity": 8,
  "occurrence": 4,
  "detection": 5,
  "rpn": 160,
  "mitigations": [
    "Watchdog monitoring on slip-detection task",
    "Redundant wheel speed sensor input path",
    "End-of-line ABS activation test before vehicle delivery"
  ],
  "justifications": {
    "severity": "Failure to activate ABS during emergency braking can cause loss of directional control and significant injury risk — ASIL B item.",
    "occurrence": "ADC signal corruption or watchdog reset is a low-probability systematic defect in a mature ECU design.",
    "detection": "No continuous runtime monitoring of pump-activation response stated in parent requirement; EoL test improves but does not eliminate in-field detection gap."
  }
}
```

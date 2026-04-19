---
name: pharaoh-flow
description: Orchestrate the full V-model chain for one feature context — requirement → architecture element → verification plan → FMEA, each with a review pass. Invokes pharaoh-req-draft, pharaoh-req-review, pharaoh-arch-draft, pharaoh-arch-review, pharaoh-vplan-draft, pharaoh-vplan-review, pharaoh-fmea in sequence.
chains_from: []
chains_to: []
---

# pharaoh-flow

## When to use

Invoke when the user wants to produce a complete V-model artefact chain from a single feature
context in one operation. This skill orchestrates the seven atomic skills; it does not author
content itself.

**Scope is exactly:** one feature context → one `gd_req` + one `arch` element + one `tc` test
case + one `fmea` entry, with a review pass after the requirement and architecture steps.

Do NOT invoke when the user wants to draft only one artefact type — use the individual atomic
skills directly. Do NOT invoke when the feature context implies multiple requirements (the
orchestrator will draft the single most direct requirement and advise re-invocation).

> This is a compositional orchestrator. The atomicity criterion (a) does not apply: by design
> it invokes multiple skills. Scope is bounded to "one feature → one V-model chain".

---

## Inputs

- **feature_context** (from user): short prose describing the feature (1–5 sentences), target
  level, safety relevance
- **parent_link** (from user): ID of the parent requirement or workflow the new requirement
  will satisfy
- **safety_context** (from user, optional): ASIL level (A–D) or safety goal if known — passed
  through to `pharaoh-fmea`
- **tailoring** (from `.pharaoh/project/`): same tailoring files read by each atomic skill
- **needs.json**: required for parent resolution and uniqueness checks in each sub-skill

---

## Outputs

Four artefacts + up to two review finding reports, each in a labeled fenced block:

```
=== [ARTEFACT 1] gd_req: <id> ===
<RST directive block>

=== [REVIEW 1] req-review: <id> ===
<findings JSON>

=== [ARTEFACT 2] arch: <id> ===
<RST directive block>

=== [REVIEW 2] arch-review: <id> ===
<findings JSON>

=== [ARTEFACT 3] tc: <id> ===
<RST directive block>

=== [ARTEFACT 4] fmea: <id> ===
<FMEA JSON>

=== [FLOW SUMMARY] ===
<summary JSON>
```

**Flow summary shape:**

```json
{
  "feature_context_summary": "one sentence",
  "artefacts": {
    "gd_req":  {"id": "gd_req__...",  "overall": "pass|needs_work|fail"},
    "arch":    {"id": "arch__...",    "overall": "pass|needs_work|fail"},
    "tc":      {"id": "tc__...",      "status": "drafted"},
    "fmea":    {"id": "fmea__...",    "rpn": 160}
  },
  "reviews": {
    "req_review":  "pass|needs_work|fail",
    "arch_review": "pass|needs_work|fail"
  },
  "stop_reason": null
}
```

If the chain was stopped early (see Guardrail G2), `stop_reason` contains the diagnostic from
the failing skill.

---

## Process

### Step 0: Validate inputs

Confirm `feature_context` and `parent_link` are provided. If either is missing, FAIL before
invoking any sub-skill:

```
FAIL: pharaoh-flow requires feature_context and parent_link.
Provide both before invoking the orchestrator.
```

---

### Step 1: Draft requirement — invoke pharaoh-req-draft

Pass `feature_context`, `parent_link`, and tailoring to `pharaoh-req-draft`. Capture output.

If `pharaoh-req-draft` returns a FAIL (not a `[DIAGNOSTIC]`), stop the chain:
emit the failure in a `=== [CHAIN STOP: req-draft] ===` block and set `stop_reason` in the
summary. Do not proceed to Step 2.

---

### Step 2: Review requirement — invoke pharaoh-req-review

Pass the RST block from Step 1 to `pharaoh-req-review`. Capture findings JSON.

If `pharaoh-req-review` returns a hard FAIL (unresolved target), stop the chain.

If `overall` is `"needs_work"` or `"fail"`, **do not stop** — continue the chain but record
the review result in the summary. The user can address the action items independently.

---

### Step 3: Draft architecture element — invoke pharaoh-arch-draft

Pass `feature_context`, the `gd_req` ID from Step 1, and tailoring to `pharaoh-arch-draft`.

If `pharaoh-arch-draft` returns a FAIL, stop the chain and record `stop_reason`.

---

### Step 4: Review architecture element — invoke pharaoh-arch-review

Pass the RST block from Step 3 to `pharaoh-arch-review`. Capture findings JSON.

Same policy as Step 2: `needs_work` or `fail` does not stop the chain.

---

### Step 5: Draft verification plan — invoke pharaoh-vplan-draft

Pass the `gd_req` ID from Step 1 (primary parent for the test case) and tailoring to
`pharaoh-vplan-draft`.

If `pharaoh-vplan-draft` returns a FAIL, emit a warning block but do not stop the full chain:

```
=== [WARNING: vplan-draft failed] ===
<FAIL message>
tc artefact will be absent from the summary.
```

Record `tc: null` in the summary.

---

### Step 6: Draft FMEA entry — invoke pharaoh-fmea

Pass the `gd_req` ID from Step 1 as `parent_id`, and `safety_context` if provided, to
`pharaoh-fmea`.

If `pharaoh-fmea` returns a FAIL, emit a warning block but do not stop:

```
=== [WARNING: fmea failed] ===
<FAIL message>
fmea artefact will be absent from the summary.
```

Record `fmea: null` in the summary.

---

### Step 7: Emit all outputs and flow summary

Emit each artefact and review in its labeled fenced block in the order shown in the Outputs
section. Emit the flow summary last.

---

## Guardrails

**G1 — Missing required inputs**

`feature_context` or `parent_link` absent → FAIL before any sub-skill runs (Step 0).

**G2 — Hard failure in req-draft or arch-draft**

These two steps are load-bearing. If either returns a hard FAIL, stop and record `stop_reason`.
The vplan and fmea steps are best-effort (warnings but not chain stops).

**G3 — Review findings don't block chain**

A review returning `overall: fail` is informational — the chain continues. The action items
are preserved in the review block for the user to address. The orchestrator does not
auto-regenerate; that would require `pharaoh-req-regenerate`.

**G4 — Tailoring unavailable**

If `.pharaoh/project/` tailoring files are missing, the sub-skills will fail. Fail fast with:

```
FAIL: pharaoh-flow cannot run without tailoring files at .pharaoh/project/.
Run pharaoh-tailor-detect → pharaoh-tailor-fill first.
```

---

## Advisory chain

This skill has `chains_to: []` — it is a terminal orchestrator. After the flow summary, advise
only if reviews returned action items:

```
Review action items in [REVIEW 1] and [REVIEW 2] blocks.
Use `pharaoh-req-regenerate` or `pharaoh-arch-draft` (with corrections) to address them.
```

---

## Worked example

**User input:**
> feature_context: "The brake controller shall engage the ABS pump when wheel slip exceeds a
> calibrated threshold. Target level: component. Safety relevance: ASIL B."
> parent_link: `wf__brake_system_design`
> safety_context: ASIL B

**Step 0:** both inputs present. Continue.

**Step 1 — req-draft:** produces `gd_req__abs_pump_activation`.

**Step 2 — req-review:** all axes pass → `overall: pass`.

**Step 3 — arch-draft:** produces `arch__brake_controller_abs_module` satisfying
`gd_req__abs_pump_activation`.

**Step 4 — arch-review:** all axes pass → `overall: pass`.

**Step 5 — vplan-draft:** produces `tc__abs_pump_activation_001` verifying
`gd_req__abs_pump_activation`.

**Step 6 — fmea:** produces `fmea__abs_pump_activation__no_activation`; RPN = 160.

**Step 7 output (condensed):**

```
=== [ARTEFACT 1] gd_req: gd_req__abs_pump_activation ===
.. gd_req:: ABS pump activation on wheel slip threshold
   :id: gd_req__abs_pump_activation
   :status: draft
   :satisfies: wf__brake_system_design
   :verification: tc__abs_pump_activation_001

   The brake controller shall engage the ABS pump when measured wheel slip exceeds
   the calibrated activation threshold.

=== [REVIEW 1] req-review: gd_req__abs_pump_activation ===
{"need_id": "gd_req__abs_pump_activation", "overall": "pass", "action_items": [], ...}

=== [ARTEFACT 2] arch: arch__brake_controller_abs_module ===
.. arch:: Brake Controller ABS Module
   :id: arch__brake_controller_abs_module
   :status: draft
   :satisfies: gd_req__abs_pump_activation
   :type: component

   The ABS module within the brake controller monitors wheel-slip signals and activates
   the ABS pump actuator when the slip threshold is exceeded.

=== [REVIEW 2] arch-review: arch__brake_controller_abs_module ===
{"need_id": "arch__brake_controller_abs_module", "overall": "pass", "action_items": [], ...}

=== [ARTEFACT 3] tc: tc__abs_pump_activation_001 ===
.. tc:: ABS pump activation on wheel slip threshold — functional test
   :id: tc__abs_pump_activation_001
   :status: draft
   :verifies: gd_req__abs_pump_activation

   Inputs
   ------
   Simulated wheel-speed sensor signals producing slip > calibrated threshold.

   Steps
   -----
   1. Inject slip-threshold-exceedance signal.
   2. Observe ABS pump actuator output.

   Expected
   --------
   ABS pump activates within 10 ms of threshold exceedance.

=== [ARTEFACT 4] fmea: fmea__abs_pump_activation__no_activation ===
{"fmea_id": "fmea__abs_pump_activation__no_activation", "rpn": 160, ...}

=== [FLOW SUMMARY] ===
{
  "feature_context_summary": "Brake controller engages ABS pump on wheel-slip threshold exceedance (ASIL B)",
  "artefacts": {
    "gd_req": {"id": "gd_req__abs_pump_activation",             "overall": "pass"},
    "arch":   {"id": "arch__brake_controller_abs_module",       "overall": "pass"},
    "tc":     {"id": "tc__abs_pump_activation_001",             "status": "drafted"},
    "fmea":   {"id": "fmea__abs_pump_activation__no_activation","rpn": 160}
  },
  "reviews": {
    "req_review":  "pass",
    "arch_review": "pass"
  },
  "stop_reason": null
}
```

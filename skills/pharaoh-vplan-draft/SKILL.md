---
name: pharaoh-vplan-draft
description: Use when drafting a single sphinx-needs test-case (verification plan item) for one requirement. Emits an RST tc__ directive with inputs, steps, and expected outcome, linking to the parent req via :verifies:.
chains_from: [pharaoh-req-draft, pharaoh-req-regenerate, pharaoh-arch-draft]
chains_to: [pharaoh-vplan-review]
---

# pharaoh-vplan-draft

## When to use

Invoke when the user has a validated requirement (or architecture element) and wants to derive a
single test case that verifies it. Each invocation produces exactly one `tc__` directive.

Do NOT draft multiple test cases in one invocation — one test case per call.
Do NOT draft test cases for requirements that are not verifiable (see Guardrail G3).
Do NOT review — use `pharaoh-vplan-review` after drafting.

---

## Inputs

- **parent_id** (from user): need-id of the parent requirement or architecture element to verify
  — must exist in needs.json
- **verification_level** (from user): one of `unit`, `integration`, or `system`
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — look up the `tc` entry if it exists; fall back to prefix `tc__`
    and default required fields if absent
  - `id-conventions.yaml` — prefix, separator, id_regex
- **needs.json**: required for parent resolution and ID uniqueness

> Note: A `shared/tailoring-access.md` helper module is planned. Until it exists, Steps 1-2 below
> inline the tailoring-access logic directly. When that file is created, this skill should be
> updated to delegate to it.

---

## Outputs

A single RST `tc__` directive block containing:

- Unique ID per id-conventions (prefix `tc__` unless catalog overrides)
- `:status: draft`
- `:verifies:` pointing to parent_id (validated in needs.json)
- `:level:` set to the requested verification_level (`unit` / `integration` / `system`)
- Body with three labelled sections: **Inputs**, **Steps**, **Expected**

The body must be self-contained — a test engineer should be able to execute this test case
without reading any other document beyond the referenced parent requirement.

---

## Process

### Step 1: Read tailoring

**1a. `artefact-catalog.yaml`**

Look up the `tc` entry. If found, read `required_fields`, `optional_fields`, `lifecycle`.

If the `tc` entry does not exist, use these defaults:
- `required_fields`: `[id, status, verifies, inputs, steps, expected]`
- `optional_fields`: `[tags, rationale, level]`
- `lifecycle`: `[draft, valid, inspected]`

Note the fallback in output if defaults were applied.

**1b. `id-conventions.yaml`**

Extract `separator` and `id_regex`. Use prefix `tc__` unless the catalog specifies otherwise.

**1c. Validate verification_level**

Accepted values: `unit`, `integration`, `system`. If a different value is supplied, FAIL:

```
FAIL: verification_level "<value>" is not recognised.
Accepted values: unit, integration, system.
```

---

### Step 2: Locate and parse needs.json

Find `needs.json` (check `docs/_build/needs/needs.json`, then `_build/needs/needs.json`, then any
`needs.json` under a `_build` directory). If not found, FAIL:

```
FAIL: needs.json not found. Build the Sphinx project first (`sphinx-build docs/ docs/_build/`),
then re-run this skill.
```

Extract the flat map of `id → {id, type, status, body}` and the set of all existing IDs.

---

### Step 3: Validate parent_id

1. Look up `parent_id` in needs.json. If not found, FAIL:

```
FAIL: parent_id "<id>" not found in needs.json.
Specify an existing requirement or architecture element ID.
```

2. Extract the parent body to understand what testable claim must be verified.

3. Check whether the parent's type is testable:
   - Requirement types (prefix ends in `req`) — always valid
   - Architecture elements (prefix `arch__`) — valid at integration/system level only
   - Workflow/work-product types (`wf`, `wp`) — warn but do not block:
     ```
     [WARNING] parent_id "<id>" has type "<type>". Verification plans are usually written
     against requirements or arch elements. Proceeding at user's discretion.
     ```

---

### Step 4: Testability check

Read the parent body. Confirm that the parent contains a testable claim:
- A measurable outcome or threshold (e.g. "within X ms", "exceeds Y threshold")
- A discrete pass/fail condition (e.g. "shall activate the valve", "shall reject the input")

If the parent body is too vague to derive a verifiable procedure (e.g. body is a stub, no
condition or outcome stated), FAIL:

```
FAIL: parent "<parent_id>" does not contain a testable claim.
Improve the parent requirement first (e.g. run pharaoh-req-regenerate) before drafting a
test case.
```

---

### Step 5: Assign a unique ID

**5a. Derive local-ID part**

Format: `tc__<local>` where local is derived from the parent_id local part plus a level suffix:
- Strip the prefix from parent_id: `gd_req__abs_pump_activation` → `abs_pump_activation`
- Append `_<verification_level>`: → `abs_pump_activation_system`

Check uniqueness. If taken, append `_2`, `_3`, etc.

**5b. Validate against id_regex**

Confirm the candidate matches `id_regex`. If it does not, FAIL:

```
FAIL: generated ID "<id>" does not match id_regex "<regex>".
```

---

### Step 6: Draft the test case body

Structure the body using three labelled sections. Use a Given/When/Then framing where natural,
or a step-by-step enumeration for procedural tests.

**Inputs section** — list all preconditions and input stimuli:

```
Inputs:
- <precondition or stimulus 1>
- <precondition or stimulus 2>
```

**Steps section** — ordered procedure:

```
Steps:
1. <action>
2. <action>
3. Observe <observable outcome>
```

**Expected section** — concrete pass criterion:

```
Expected:
<Observable result that proves the parent claim is satisfied. Must be checkable without
ambiguity — state exact value, range, or behaviour.>
```

The expected outcome must directly trace to the testable claim extracted from the parent body
in Step 4. Do not invent pass criteria that are not implied by the parent.

---

### Step 7: Self-check

Before emitting:

**Check A — required fields present**
Every field in `required_fields` from Step 1 must appear.

**Check B — parent resolves**
`:verifies:` value is present in needs.json (confirmed in Step 3).

**Check C — ID unique**
Chosen ID not in needs.json.

**Check D — testable expected outcome**
Expected section must contain a concrete, unambiguous pass criterion. Vague criteria like
"the system works correctly" or "no errors occur" are not acceptable — rewrite with a specific
observable.

If any check fails after one rewrite attempt, emit with `[DIAGNOSTIC]`.

---

### Step 8: Emit the directive block

```rst
.. tc:: <test case title>
   :id: <id>
   :status: draft
   :verifies: <parent_id>
   :level: <verification_level>

   Inputs:
   - <input 1>
   - <input 2>

   Steps:
   1. <step>
   2. <step>

   Expected:
   <pass criterion>
```

If the `tc` entry was absent from artefact-catalog and defaults were applied, append:

```
[NOTE] artefact-catalog.yaml has no 'tc' entry. Prefix 'tc__' and default required fields
[id, status, verifies, inputs, steps, expected] were used. Add a 'tc' entry to
.pharaoh/project/artefact-catalog.yaml before promoting beyond draft.
```

---

## Guardrails

**G1 — Parent not found**

parent_id absent from needs.json → FAIL (Step 3).

**G2 — verification_level not recognised**

Unrecognised level value → FAIL (Step 1c).

**G3 — Parent not testable**

Parent body too vague to derive a verifiable procedure → FAIL (Step 4). Do not draft a
placeholder test case — improve the parent first.

**G4 — needs.json unavailable**

Cannot find needs.json → FAIL (Step 2).

---

## Advisory chain

After successfully emitting the directive:

```
Consider running `pharaoh-vplan-review <new_id>` to audit against per-axis criteria.
```

Do not show this if the emit included a `[DIAGNOSTIC]`.

---

## Worked example

**User input:**
> Parent: `gd_req__abs_pump_activation`; level: `system`.

**Parent body (from needs.json):**
> "The brake controller shall engage the ABS pump when measured wheel slip exceeds the calibrated
> activation threshold."

**Step 1:** No `tc` entry in artefact-catalog.yaml. Defaults applied. Level `system` is valid.

**Step 2:** needs.json found; 185 IDs loaded.

**Step 3:** `gd_req__abs_pump_activation` found; type `gd_req`. Valid.

**Step 4:** Testable claim — "engage the ABS pump when wheel slip exceeds the calibrated
activation threshold" — discrete activation event, verifiable by observing pump output signal.

**Step 5:** local = `abs_pump_activation_system`; candidate = `tc__abs_pump_activation_system`.
Not in needs.json. Passes id_regex.

**Step 6 body drafted** (see output below).

**Step 7 self-checks:** required fields present; parent resolves; ID unique; expected outcome
concrete ("ABS pump output signal activates within 50 ms"). All pass.

**Step 8 output:**

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

```
[NOTE] artefact-catalog.yaml has no 'tc' entry. Prefix 'tc__' and default required fields
[id, status, verifies, inputs, steps, expected] were used. Add a 'tc' entry to
.pharaoh/project/artefact-catalog.yaml before promoting beyond draft.

Consider running `pharaoh-vplan-review tc__abs_pump_activation_system` to audit against per-axis criteria.
```

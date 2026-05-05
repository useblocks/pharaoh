---
name: pharaoh-vplan-draft
description: Use when drafting a single sphinx-needs test-case (verification plan item) for one requirement. The artefact type is parameterised via `target_level` (any catalog-declared verification-plan / test-case type — e.g. `tc`, `test`, `vplan`). Emits an RST directive with inputs, steps, and expected outcome, linking to the parent req via `:verifies:`.
chains_from: [pharaoh-req-draft, pharaoh-req-regenerate, pharaoh-arch-draft]
chains_to: [pharaoh-vplan-review]
---

# pharaoh-vplan-draft

## When to use

Invoke when the user has a validated requirement (or architecture element) and wants to derive a
single test case that verifies it. Each invocation produces exactly one directive of the
catalog-declared verification-plan type. The directive name and ID prefix are resolved from
the project's tailoring; this skill is type-agnostic and supports any catalog-declared
verification-plan type (typical names: `tc`, `test`, `vplan`).

Do NOT draft multiple test cases in one invocation — one test case per call.
Do NOT draft test cases for requirements that are not verifiable (see Guardrail G3).
Do NOT review — use `pharaoh-vplan-review` after drafting.

---

## Inputs

- **parent_id** (from user): need-id of the parent requirement or architecture element to verify
  — must exist in needs.json
- **target_level** (from user, default `tc`): the artefact-catalog type name to emit. Any
  verification-plan / test-case type declared in `.pharaoh/project/artefact-catalog.yaml`
  is accepted. The emitted directive uses `target_level` verbatim as the directive name; the
  ID prefix is resolved from `id-conventions.yaml`'s `prefixes` map.
- **verification_level** (from user, optional, default `system`): one of `unit`, `integration`, or `system`. When the dispatching caller (e.g. `pharaoh-author`) does not propagate this input, the default applies — `system` is the broadest scope and the safest default for a top-level test case.
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — look up the entry for `target_level` to read `required_fields`,
    `optional_fields`, `lifecycle`, and `required_body_sections`
  - `id-conventions.yaml` — `prefixes` map (key = type name → value = identifier prefix
    string), `separator`, `id_regex`
- **needs.json**: required for parent resolution and ID uniqueness

> Note: A `shared/tailoring-access.md` helper module is planned. Until it exists, Steps 1-2 below
> inline the tailoring-access logic directly. When that file is created, this skill should be
> updated to delegate to it.

---

## Outputs

A single RST directive block of type `target_level` containing:

- Unique ID using the prefix resolved for `target_level` from `id-conventions.yaml`'s
  `prefixes` map
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

Look up the entry whose key equals `target_level`. If found, read `required_fields`,
`optional_fields`, `lifecycle`, and `required_body_sections`.

**`required_fields` / `optional_fields`** are directive option names (sphinx-needs `:key: value`
options). **`required_body_sections`** are top-level Markdown/RST section headings that must
appear in the directive body prose (e.g. `Inputs`, `Steps`, `Expected`).

If the entry is absent, FAIL:

```
FAIL: target_level "<value>" is not declared in .pharaoh/project/artefact-catalog.yaml.
Add an entry for "<value>" (with required_fields, required_body_sections, lifecycle) before
drafting, or pass a target_level that is already declared.
```

**1b. `id-conventions.yaml`**

Read the `prefixes:` map and look up the prefix for `target_level`. Also extract
`separator` and `id_regex`.

If `prefixes` does not declare `target_level`, FAIL:

```
FAIL: id-conventions.yaml prefixes map has no entry for "<value>".
Declare a prefix for "<value>" (e.g. T_ for a type named "test", or TC_ for "tc")
before drafting.
```

The resolved prefix is the value of `prefixes[target_level]` — e.g. `tc__` for
`target_level: tc` on a project that uses the double-underscore convention, `T_` for
`target_level: test` on a project that uses underscore separators.

**1c. Validate verification_level**

Accepted values: `unit`, `integration`, `system`. If `verification_level` is absent,
default to `system` (the broadest scope; the override is documented in the Inputs
section above). If a different non-empty value is supplied, FAIL:

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
   - Architecture elements (any catalog-declared architecture type) — valid at
     integration/system level only
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

Format: `<prefix><tail>` where `<prefix>` is the value resolved in Step 1b. The tail is
derived from the parent_id local part plus a level suffix:

- Strip the parent's prefix from `parent_id`: `gd_req__abs_pump_activation` → `abs_pump_activation`
- Append `_<verification_level>` → `abs_pump_activation_system`
- Compose the full ID by concatenating `<prefix>` + `<tail>`. If `id-conventions.yaml`
  declares an explicit `separator` distinct from any trailing punctuation in the prefix,
  insert it between prefix and tail.

Examples:

- `prefixes: {tc: tc__}` → `tc__abs_pump_activation_system`
- `prefixes: {test: T_}` → `T_abs_pump_activation_system`

Check uniqueness. If taken, append `_2`, `_3`, etc.

**5b. Validate against id_regex**

Confirm the candidate matches the `id_regex` declared in `id-conventions.yaml`. If it does
not, FAIL:

```
FAIL: generated ID "<id>" does not match id_regex "<regex>".
```

This is the gate that catches a hardcoded prefix mismatch — e.g. emitting `tc__foo_unit`
on a project whose `test` type uses prefix `T_` and a regex `^T_[A-Za-z0-9_]+$`. Because
the prefix is read from `prefixes[target_level]`, this case is now caught at draft time.

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
.. <target_level>:: <test case title>
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

The directive name is exactly `target_level`; the `:id:` value uses the prefix resolved from
`id-conventions.yaml`'s `prefixes` map. Both come from tailoring — neither is hardcoded.

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

**G5 — target_level not declared**

If `target_level` is not declared in `artefact-catalog.yaml` or has no entry in
`id-conventions.yaml`'s `prefixes` map, FAIL (Step 1 handles this). The catalog is the
contract — never silently default to a hardcoded prefix.

---

## Advisory chain

After successfully emitting the directive:

```
Consider running `pharaoh-vplan-review <new_id>` to audit against per-axis criteria.
```

Do not show this if the emit included a `[DIAGNOSTIC]`.

---

## Worked example

### Example A — default `target_level: tc`

**User input:**
> Parent: `gd_req__abs_pump_activation`; level: `system`. (`target_level` defaults to `tc`.)

**Parent body (from needs.json):**
> "The brake controller shall engage the ABS pump when measured wheel slip exceeds the calibrated
> activation threshold."

**Step 1:** Catalog has a `tc` entry with `required_fields: [id, status, verifies]` and
`required_body_sections: [Inputs, Steps, Expected]`. `id-conventions.yaml` `prefixes` map
has `tc: tc__`. Level `system` is valid.

**Step 2:** needs.json found; 185 IDs loaded.

**Step 3:** `gd_req__abs_pump_activation` found; type `gd_req`. Valid.

**Step 4:** Testable claim — "engage the ABS pump when wheel slip exceeds the calibrated
activation threshold" — discrete activation event, verifiable by observing pump output signal.

**Step 5:** prefix = `tc__`; tail = `abs_pump_activation_system`; candidate =
`tc__abs_pump_activation_system`. Not in needs.json. Passes id_regex.

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
Consider running `pharaoh-vplan-review tc__abs_pump_activation_system` to audit against per-axis criteria.
```

### Example B — project that uses `test` with prefix `T_`

**User input:**
> Parent: `req__login_lockout`; target_level: `test`; level: `unit`.

**Step 1:** Catalog has a `test` entry with `required_fields: [id, status, verifies]` and
`required_body_sections: [Inputs, Steps, Expected]`. `id-conventions.yaml` `prefixes` map
has `test: T_`. Level `unit` is valid.

**Step 5:** prefix = `T_`; tail = `login_lockout_unit`; candidate = `T_login_lockout_unit`.
Passes id_regex `^T_[A-Za-z0-9_]+$`.

**Step 8 output (header only):**

```rst
.. test:: Login lockout — unit test
   :id: T_login_lockout_unit
   :status: draft
   :verifies: req__login_lockout
   :level: unit

   ...
```

A skill that hardcoded `tc__` would have emitted `tc__login_lockout_unit`, which fails the
project's `T_…` `id_regex` at Step 5b. By deriving prefix and directive name from tailoring
the same skill serves both projects.

## Last step

After emitting the artefact, invoke `pharaoh-vplan-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must regenerate (via `pharaoh-vplan-regenerate` if available, or by re-invoking this skill with the findings as input).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

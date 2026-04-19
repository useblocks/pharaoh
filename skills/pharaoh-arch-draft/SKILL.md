---
name: pharaoh-arch-draft
description: Use when drafting a single sphinx-needs architecture element (component / interface / module) from one parent requirement. Emits an RST directive block linking back to the parent via :satisfies:.
chains_from: [pharaoh-req-draft, pharaoh-req-regenerate]
chains_to: [pharaoh-arch-review]
---

# pharaoh-arch-draft

## When to use

Invoke when the user has a validated requirement (ideally reviewed by `pharaoh-req-review`) and
wants to derive one architecture element from it. Target element types: `component`, `module`,
or `interface`.

Do NOT draft multiple architecture elements in a single invocation — one element per call.
Do NOT create architecture elements without a parent requirement — every arch element must trace
back to at least one req via `:satisfies:`.
Do NOT review — use `pharaoh-arch-review` after drafting.

---

## Inputs

- **parent_req_id** (from user): need-id of the parent requirement — must exist in needs.json
- **arch_type** (from user): one of `module`, `component`, or `interface`
- **element_description** (from user): 1-3 sentences describing the element's responsibility
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — look up the `arch` entry if it exists; fall back to placeholder
    prefix `arch__` if the entry is absent
  - `id-conventions.yaml` — prefix, separator, id_regex
- **needs.json**: required for parent resolution and ID uniqueness

> Note: A `shared/tailoring-access.md` helper module is planned. Until it exists, Steps 1-2 below
> inline the tailoring-access logic directly. When that file is created, this skill should be
> updated to delegate to it.

---

## Outputs

A single RST directive block for the architecture element, containing:

- Unique ID using the project's arch prefix (from artefact-catalog `arch` entry) or `arch__` if
  no entry exists
- `:status: draft`
- `:satisfies:` pointing to parent_req_id
- `:type:` set to the requested arch_type (`module` / `component` / `interface`)
- Body: 1-3 sentences describing the element's responsibility; no `shall` — architecture elements
  state what something *is*, not what it *shall do* (requirements do that)

---

## Process

### Step 1: Read tailoring

**1a. `artefact-catalog.yaml`**

Look up the `arch` entry. If found, read:
- `required_fields` — fields that must be present
- `optional_fields` — fields that may be added
- `lifecycle` — valid `:status:` values

If the `arch` entry does not exist (likely for Score until the catalog extension commit), use these
defaults:
- `required_fields`: `[id, status, satisfies, type]`
- `optional_fields`: `[tags, rationale, description]`
- `lifecycle`: `[draft, valid, inspected]`

Note the fallback in output if defaults were applied.

**1b. `id-conventions.yaml`**

Extract `separator` and `id_regex`. Determine the arch prefix:
- If artefact-catalog has an `arch` entry with a prefix key, use it
- Otherwise use `arch__` (two underscores, matching Score id convention)

**1c. Validate arch_type**

Accepted values: `module`, `component`, `interface`. If the user supplies a different value, FAIL:

```
FAIL: arch_type "<value>" is not recognised.
Accepted values: module, component, interface.
```

---

### Step 2: Locate and parse needs.json

Find `needs.json` (check `docs/_build/needs/needs.json`, then `_build/needs/needs.json`, then
any `needs.json` under a `_build` directory). If not found, FAIL:

```
FAIL: needs.json not found. Build the Sphinx project first (`sphinx-build docs/ docs/_build/`),
then re-run this skill.
```

Extract a flat map of `id → {id, type, status}` and the set of all existing IDs.

---

### Step 3: Validate parent_req_id

1. Look up `parent_req_id` in the needs.json map. If not found, FAIL:

```
FAIL: parent_req_id "<id>" not found in needs.json.
Specify an existing requirement ID or build the project first.
```

2. Confirm the parent is a requirement type (prefix ends in `req` or `_req`). If it is a
   different type (e.g. `wf`, `wp`), warn but do not block:

```
[WARNING] parent_req_id "<id>" has type "<type>" which is not a requirement.
Architecture elements should trace to requirements. Proceeding at user's discretion.
```

---

### Step 4: Assign a unique ID

**4a. Derive local-ID part**

Format: `<prefix><separator><local>` where local is derived from `element_description`:
- Lowercase, words separated by underscores
- Maximum 5 words; trim articles, prepositions, conjunctions
- Example: "Power management module for ECU startup" → local `power_management_module`

Prepend arch_type as first word if the local part does not already imply the type:
- `module` → local starts with `mod_` if not already
- `component` → no additional prefix (component is the default)
- `interface` → local starts with `if_` if not already

**4b. Check uniqueness**

Candidate = `<prefix><separator><local>`. If already in needs.json ID set, append `_2`, `_3`, etc.

**4c. Validate against id_regex**

If the candidate does not match, FAIL:

```
FAIL: generated ID "<id>" does not match id_regex "<regex>".
Revise element_description to use lowercase ASCII words.
```

---

### Step 5: Draft the element body

Write 1-3 sentences describing:
1. What the element *is* (its role in the system)
2. What it contains or depends on (if known from parent req)
3. Its boundary (what it does NOT include) — only if the parent req implies a clear scope limit

Do NOT use `shall` in the body. Architecture descriptions use present tense: "The X module
manages Y" / "The X interface provides Z".

Single-responsibility check: the description must describe one coherent unit. If
`element_description` implies multiple distinct concerns (e.g. "handles user authentication AND
logs all activity"), FAIL:

```
FAIL: element_description describes multiple responsibilities.
Invoke pharaoh-arch-draft once per responsibility.
Primary responsibility identified: "<extracted primary>".
```

---

### Step 6: Self-check

Before emitting:

**Check A — required fields present**
Every field in `required_fields` from Step 1 must appear in the directive.

**Check B — parent resolves**
`:satisfies:` value is present in needs.json (confirmed in Step 3).

**Check C — ID unique**
Chosen ID not in needs.json (confirmed in Step 4).

**Check D — no `shall` in body**
Body must not contain `shall`. If found, rewrite in descriptive present tense.

If any check fails after one rewrite attempt, emit with `[DIAGNOSTIC]`:

```
[DIAGNOSTIC] Self-check "<check name>" failed after rewrite.
Manual correction required before running pharaoh-arch-review.
```

---

### Step 7: Emit the directive block

```rst
.. arch:: <element title>
   :id: <id>
   :status: draft
   :satisfies: <parent_req_id>
   :type: <arch_type>

   <1-3 sentence description>
```

If the tailoring fallback was applied (no `arch` entry in catalog), append:

```
[NOTE] artefact-catalog.yaml has no 'arch' entry. Prefix 'arch__' and default required fields
[id, status, satisfies, type] were used. Run the catalog extension commit or add an 'arch' entry
to .pharaoh/project/artefact-catalog.yaml before promoting this element beyond draft.
```

---

## Guardrails

**G1 — Parent not found**

If parent_req_id is absent from needs.json, FAIL immediately (Step 3 handles this).

**G2 — Multiple responsibilities**

If element_description covers more than one distinct concern, FAIL (Step 5 handles this). Do not
silently draft a compound element.

**G3 — arch_type not recognised**

If arch_type is not `module`, `component`, or `interface`, FAIL (Step 1c handles this).

**G4 — needs.json unavailable**

If needs.json cannot be found, FAIL and instruct the user to build first (Step 2 handles this).

---

## Advisory chain

After successfully emitting the directive:

```
Consider running `pharaoh-arch-review <new_id>` to audit against ISO 26262-8 §6 axes.
```

Do not show this if the emit included a `[DIAGNOSTIC]`.

---

## Worked example

**User input:**
> Parent: `gd_req__abs_pump_activation`; type: `component`; description: "Manages the ABS pump
> drive circuit, including PWM duty-cycle control and over-current protection."

**Step 1:** No `arch` entry found in artefact-catalog.yaml. Falling back to defaults: prefix
`arch__`, required `[id, status, satisfies, type]`. arch_type `component` is valid.

**Step 2:** needs.json found at `docs/_build/needs/needs.json`; 185 IDs loaded.

**Step 3:** `gd_req__abs_pump_activation` found in needs.json; type `gd_req`. Parent valid.

**Step 4:** local derived: `abs_pump_driver`. Candidate: `arch__abs_pump_driver`. Not in
needs.json. Passes id_regex `^[a-z][a-z_]*__[a-z0-9_]+$`. ID assigned.

**Step 5:** Single responsibility — manages ABS pump drive circuit only. No `shall` in body. OK.

**Step 6:** All checks pass.

**Step 7 output:**

```rst
.. arch:: ABS pump driver component
   :id: arch__abs_pump_driver
   :status: draft
   :satisfies: gd_req__abs_pump_activation
   :type: component

   The ABS pump driver component manages the pump drive circuit, controlling output
   PWM duty cycle and providing over-current protection for the pump motor.
```

```
[NOTE] artefact-catalog.yaml has no 'arch' entry. Prefix 'arch__' and default required fields
[id, status, satisfies, type] were used. Run the catalog extension commit or add an 'arch' entry
to .pharaoh/project/artefact-catalog.yaml before promoting this element beyond draft.

Consider running `pharaoh-arch-review arch__abs_pump_driver` to audit against ISO 26262-8 §6 axes.
```

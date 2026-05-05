---
name: pharaoh-arch-draft
description: Use when drafting a single sphinx-needs architecture element from one parent requirement. The artefact type is parameterised via `target_level` (any catalog-declared architecture type — e.g. `arch`, `swarch`, `sys-arch`, `module`, `component`, `interface`). Emits an RST directive block linking back to the parent via `:satisfies:`.
chains_from: [pharaoh-req-draft, pharaoh-req-regenerate]
chains_to: [pharaoh-arch-review]
---

# pharaoh-arch-draft

## When to use

Invoke when the user has a validated requirement (ideally reviewed by `pharaoh-req-review`) and
wants to derive one architecture element from it. The element's directive name and ID prefix
come from the project's `artefact-catalog.yaml` / `id-conventions.yaml`; this skill is
type-agnostic and supports any architecture-shaped type the catalog declares
(`arch`, `swarch`, `sys-arch`, `module`, `component`, `interface`, …).

Do NOT draft multiple architecture elements in a single invocation — one element per call.
Do NOT create architecture elements without a parent requirement — every arch element must trace
back to at least one req via `:satisfies:`.
Do NOT review — use `pharaoh-arch-review` after drafting.

---

## Inputs

- **parent_req_id** (from user): need-id of the parent requirement — must exist in needs.json
- **target_level** (from user): the artefact-catalog type name to emit. Any type declared in
  `.pharaoh/project/artefact-catalog.yaml` is accepted (typical examples: `arch`, `swarch`,
  `sys-arch`, `module`, `component`, `interface`). The emitted directive uses `target_level`
  verbatim as the directive name; the ID prefix is resolved from the catalog / id-conventions.
- **element_description** (from user): 1-3 sentences describing the element's responsibility
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — look up the entry for `target_level` to read `required_fields`,
    `optional_fields`, and `lifecycle`
  - `id-conventions.yaml` — `prefixes` map (key = type name → value = identifier prefix
    string), `separator`, `id_regex`
- **needs.json**: required for parent resolution and ID uniqueness

> Note: A `shared/tailoring-access.md` helper module is planned. Until it exists, Steps 1-2 below
> inline the tailoring-access logic directly. When that file is created, this skill should be
> updated to delegate to it.

---

## Outputs

A single RST directive block for the architecture element, containing:

- Unique ID using the prefix resolved for `target_level` from `id-conventions.yaml`
- `:status: draft`
- `:satisfies:` pointing to parent_req_id
- Every field listed in the catalog entry's `required_fields` (the directive name itself
  carries the type, so a separate `:type:` option is only emitted when the catalog entry
  declares it as required)
- Body: 1-3 sentences describing the element's responsibility; no `shall` — architecture elements
  state what something *is*, not what it *shall do* (requirements do that)

---

## Process

### Step 1: Read tailoring

**1a. `artefact-catalog.yaml`**

Look up the entry whose key equals `target_level`. If found, read:

- `required_fields` — fields that must be present in the emitted directive
- `optional_fields` — fields that may be added
- `lifecycle` — valid `:status:` values

If the entry is absent, FAIL:

```
FAIL: target_level "<value>" is not declared in .pharaoh/project/artefact-catalog.yaml.
Add an entry for "<value>" (with required_fields, optional_fields, lifecycle) before
drafting, or pass a target_level that is already declared.
```

**1b. `id-conventions.yaml`**

Read the `prefixes:` map and look up the prefix for `target_level`. Also extract
`separator` and `id_regex`.

If `prefixes` does not declare `target_level`, FAIL:

```
FAIL: id-conventions.yaml prefixes map has no entry for "<value>".
Declare a prefix for "<value>" (e.g. SWARCH_) before drafting.
```

The resolved prefix is the value of `prefixes[target_level]`.

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

Format: `<prefix><local>` where `<prefix>` is the value resolved in Step 1b. The local part
is derived from `element_description`:

- Lowercase, words separated by underscores
- Maximum 5 words; trim articles, prepositions, conjunctions
- Example: "Power management module for ECU startup" → local `power_management_module`

**4b. Check uniqueness**

Candidate = `<prefix><local>` (or `<prefix><separator><local>` if `id-conventions.yaml`
declares an explicit separator distinct from the prefix's trailing punctuation).
If the candidate is already in the needs.json ID set, append `_2`, `_3`, etc.

**4c. Validate against id_regex**

If the candidate does not match the `id_regex` declared in `id-conventions.yaml`, FAIL:

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
.. <target_level>:: <element title>
   :id: <id>
   :status: draft
   :satisfies: <parent_req_id>

   <1-3 sentence description>
```

Add any catalog-declared `required_fields` not already shown above (the catalog is the source
of truth — emit every field it lists).

---

## Guardrails

**G1 — Parent not found**

If parent_req_id is absent from needs.json, FAIL immediately (Step 3 handles this).

**G2 — Multiple responsibilities**

If element_description covers more than one distinct concern, FAIL (Step 5 handles this). Do not
silently draft a compound element.

**G3 — target_level not declared**

If `target_level` is not declared in `artefact-catalog.yaml` or has no entry in
`id-conventions.yaml`'s `prefixes` map, FAIL (Step 1 handles this). Do not silently fall
back to a hardcoded default — the catalog is the contract.

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
> Parent: `gd_req__abs_pump_activation`; target_level: `arch`; description: "Manages the ABS
> pump drive circuit, including PWM duty-cycle control and over-current protection."

**Step 1:** `artefact-catalog.yaml` has an `arch` entry with `required_fields:
[id, status, satisfies]`. `id-conventions.yaml` `prefixes` map has `arch: arch__`.

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

   The ABS pump driver component manages the pump drive circuit, controlling output
   PWM duty cycle and providing over-current protection for the pump motor.
```

```
Consider running `pharaoh-arch-review arch__abs_pump_driver` to audit against ISO 26262-8 §6 axes.
```

For a project that distinguishes system-level and software-level architecture, the same skill
serves both — pass `target_level: sys-arch` to draft a system architecture element, or
`target_level: swarch` for a software architecture element. The directive name and prefix come
from the project's catalog and id-conventions; nothing in this skill is hardcoded to the three
classical names `module` / `component` / `interface`.

## Last step

After emitting the artefact, invoke `pharaoh-arch-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must address the action items and re-invoke this skill with the revised target as input.

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

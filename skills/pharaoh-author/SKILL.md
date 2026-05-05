---
name: pharaoh-author
description: Use when authoring or modifying a single sphinx-needs artefact (requirement, architecture element, test case, decision) by routing to the matching atomic drafting skill based on the project's artefact catalog. Returns the drafted RST directive with an ID, file placement suggestion, and parent link.
chains_from: [pharaoh-change, pharaoh-plan, pharaoh-spec]
chains_to: [pharaoh-verify]
---

# pharaoh-author

## When to use

Invoke when the user wants to create or modify one sphinx-needs artefact (one need per call)
and needs the right atomic drafting skill picked for them based on the artefact type.

This skill is a thin type-router. It does not author content itself — it dispatches to one of
the atomic drafting skills (`pharaoh-req-draft`, `pharaoh-arch-draft`, `pharaoh-vplan-draft`,
`pharaoh-decide`) and forwards their RST output verbatim, plus a file-placement hint and the
parent link.

Do NOT use when:

- The user wants the full V-model chain in one call — use `pharaoh-flow`.
- The user wants to draft multiple artefacts at once — invoke this skill once per artefact.
- The user wants to review or verify content — use `pharaoh-req-review`, `pharaoh-arch-review`,
  or `pharaoh-verify` instead.

> This is a compositional orchestrator. The atomicity criterion (a) does not apply: by design
> it dispatches to one atomic skill. Scope is bounded to "one artefact → one drafted directive".

---

## Inputs

- **target_type** (from user or inferred): the artefact type to draft. Recognised values come
  from `.pharaoh/project/artefact-catalog.yaml`. Common values: `req`, `gd_req`, `arch`,
  `tc`, `decision`. Synonyms are tolerated — e.g. `requirement` → `req`/`gd_req`,
  `architecture` / `spec` → `arch`, `test_case` / `verification` → `tc`.
- **target_id** (optional): if the user is modifying an existing need, the need-id to update.
  When absent, the dispatched drafter generates a fresh ID.
- **draft_seed** (from user): short prose describing what to author. Forwarded as
  `feature_context` / `element_description` / parent claim depending on the dispatch target.
- **parent_link** (from user, required for everything except top-level requirements and
  decisions): the need-id this artefact will trace to via `:satisfies:` or `:verifies:`.
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — used to resolve `target_type` to a known prefix and confirm a
    drafter is available
  - `id-conventions.yaml` — read by the dispatched drafter (not by this skill directly)
- **needs.json**: required by every dispatched drafter for parent resolution and ID uniqueness

---

## Outputs

The drafted RST directive block exactly as produced by the dispatched skill, plus a thin
authoring-summary block:

```
=== [ARTEFACT] <type>: <id> ===
<RST directive block from the dispatched drafter>

=== [AUTHORING SUMMARY] ===
{
  "need_id": "<id>",
  "type": "<resolved target_type>",
  "dispatched_skill": "pharaoh-req-draft|pharaoh-arch-draft|pharaoh-vplan-draft|pharaoh-decide",
  "parent_link": "<id or null>",
  "file_placement": "<suggested .rst path>",
  "stop_reason": null
}
```

If the dispatched drafter returns a hard FAIL or `[DIAGNOSTIC]`, forward it verbatim and set
`stop_reason` in the summary.

---

## Process

### Step 0: Resolve target_type

Normalise the user-supplied type to a catalog key:

| User input (any case) | Resolves to |
|---|---|
| `req`, `requirement`, `gd_req`, `comp_req`, `feat` | first matching key in artefact-catalog whose suffix is `req` (or `feat` for feature-level) |
| `arch`, `architecture`, `spec`, `specification`, `module`, `component`, `interface` | `arch` |
| `tc`, `test_case`, `test`, `verification_plan`, `vplan` | `tc` |
| `decision`, `dec`, `adr` | `decision` |

If the user's input does not map to a key present in `.pharaoh/project/artefact-catalog.yaml`,
emit:

```
FAIL: target_type "<value>" is not in the project's artefact catalog.
Catalog keys available: <list>.
```

Read `.pharaoh/project/artefact-catalog.yaml` to confirm the resolved key exists. If the
catalog file is missing, fall back to the bundled defaults — `gd_req`, `arch`, `tc` — and note
the fallback in the authoring summary.

---

### Step 1: Select the dispatch skill

Apply the routing table:

| Resolved key | Dispatched skill | Notes |
|---|---|---|
| `req`, `gd_req`, `comp_req`, `feat`, or any key whose suffix is `req` | `pharaoh-req-draft` | |
| any catalog key categorised as architecture (e.g. `arch`, `swarch`, `sys-arch`, `module`, `component`, `interface`) | `pharaoh-arch-draft` | type-agnostic; `target_level` forwarded verbatim |
| any catalog key categorised as verification-plan / test-case (e.g. `tc`, `test`, `vplan`) | `pharaoh-vplan-draft` | type-agnostic; `target_level` forwarded verbatim |
| `decision` | `pharaoh-decide` | |

Categorisation is read from the `category` field of each entry in
`.pharaoh/project/artefact-catalog.yaml` when present. When the catalog does not declare
a category, the resolution table in Step 0 above applies (e.g. `architecture` /
`specification` / `module` / `component` / `interface` user inputs all resolve to the
architecture category; `test_case` / `verification_plan` / `vplan` resolve to the
verification-plan category). The router never matches on a hardcoded type-name allow-list —
any catalog-declared type in the right category routes correctly.

If the resolved key matches none of the above (typical for safety-V types like `hazard`,
`safety_goal`, `fsr`, `tsr`), emit a clear pointer to the future safety-V drafting work and
stop:

```
FAIL: no atomic drafter is registered for target_type "<resolved key>" yet.
The author router covers req-shaped, arch-shaped, vplan-shaped, and decision types today.
Safety-V drafters (hazard, safety_goal, fsr, tsr) are tracked under issue #13 §9c. Until
they land, draft this artefact manually or extend pharaoh-author with a new dispatch entry
once the drafter exists.
```

These routing entries were thin passthroughs in the initial `pharaoh-author` commit. This
update reflects the parameterised interfaces of the two drafting skills — both
`pharaoh-arch-draft` and `pharaoh-vplan-draft` now accept any catalog-declared type via
`target_level` (no more hardcoded `arch_type ∈ {module, component, interface}` allow-list,
no more hardcoded `tc__` prefix). The router forwards `target_level` verbatim and lets the
drafter resolve prefix and required fields from `artefact-catalog.yaml` /
`id-conventions.yaml`.

---

### Step 2: Forward inputs to the dispatched skill

Pack a minimal input set per skill and invoke it. Pass through any field the user supplied;
let the dispatched skill apply its own defaults and FAIL when its inputs are insufficient.

**`pharaoh-req-draft`**

- `feature_context` ← `draft_seed`
- `parent_link` ← `parent_link` (may be a workflow-id when drafting a top-level requirement)

**`pharaoh-arch-draft`**

- `parent_req_id` ← `parent_link`
- `target_level` ← the resolved catalog key from Step 0 (e.g. `arch`, `swarch`, `sys-arch`,
  `module`, `component`, `interface`). The drafter looks up the entry in
  `artefact-catalog.yaml` and the prefix in `id-conventions.yaml`; if either is missing it
  FAILs with a clear "type X not declared" message
- `element_description` ← `draft_seed`

**`pharaoh-vplan-draft`**

- `parent_id` ← `parent_link`
- `target_level` ← the resolved catalog key from Step 0 (e.g. `tc`, `test`, `vplan`). The
  drafter derives the directive name from `target_level` and the ID prefix from
  `id-conventions.yaml`'s `prefixes` map — a project whose `test` type uses prefix `T_`
  emits compliant `T_…` IDs without modifying the skill
- `verification_level` ← user-supplied if present (`unit` / `integration` / `system`); the
  drafter will FAIL on a missing or unrecognised value

**`pharaoh-decide`**

- forward `draft_seed`, the `:decides:` link list (parsed from `parent_link` — comma-separated
  is supported), and any `decided_by` / `alternatives` / `rationale` provided by the caller

If the caller provides additional fields (e.g. `safety_context`, `tags`, `level`), forward
them as-is. The dispatched skill ignores keys it does not recognise.

---

### Step 3: Capture the drafter output

Capture the full output of the dispatched skill — the RST directive block plus any
`[NOTE]` / `[DIAGNOSTIC]` annotations.

If the dispatched skill returned a hard FAIL, propagate it verbatim and set
`stop_reason = "<dispatched-skill> FAIL"` in the authoring summary. Do not attempt to fix
the inputs and retry — the caller decides.

---

### Step 4: File placement

Suggest where to write the new RST directive. The author router does not write files — it
only suggests a path that the caller can use.

Default placement rules:

| Dispatched skill | Suggested file |
|---|---|
| `pharaoh-req-draft` | same directory as `parent_link`'s source file; filename matching the project's existing convention (e.g. `requirements.rst`) |
| `pharaoh-arch-draft` | sibling `architecture.rst` in the same directory as `parent_link`'s source |
| `pharaoh-vplan-draft` | `tests/` subdirectory if one exists, else sibling `tests.rst` |
| `pharaoh-decide` | `decisions.rst` next to the first `:decides:` target |

If `parent_link` is empty or its source location cannot be resolved from `needs.json`, emit
`file_placement: null` and let the caller decide.

---

### Step 5: Emit the authoring summary

Emit the `=== [ARTEFACT] ===` block followed by the `=== [AUTHORING SUMMARY] ===` JSON. No
prose wrapper.

If the dispatched drafter advised a follow-up (e.g. `pharaoh-arch-review`), preserve that
line below the summary so callers can chain.

---

## Guardrails

**G1 — Unknown target_type**

If the resolved key is not in the artefact catalog, FAIL (Step 0). Do not invent a new
artefact type at runtime.

**G2 — No drafter for known type**

If the resolved key is in the catalog but the routing table has no entry, FAIL with a pointer
to the future safety-V drafting work (Step 1). Do not silently fall back to `pharaoh-req-draft`.

**G3 — Dispatched drafter failed**

Forward FAIL / `[DIAGNOSTIC]` verbatim. Record `stop_reason` in the summary. Do not retry.

**G4 — Tailoring missing**

If `.pharaoh/project/artefact-catalog.yaml` is absent, the dispatched drafter will operate on
its built-in defaults. Note the fallback in the authoring summary so the caller knows the
output is not catalog-validated.

---

## Advisory chain

After a successful authoring summary, advise the caller:

```
Consider running `pharaoh-verify <need_id>` to confirm the drafted artefact
addresses the substance of its parent. For a per-axis review of the prose itself,
use `pharaoh-req-review` / `pharaoh-arch-review` / `pharaoh-vplan-review`.
```

---

## Worked example

**User input:**

> target_type: `arch`
> draft_seed: "Manages the ABS pump drive circuit, including PWM duty-cycle control and
> over-current protection."
> parent_link: `gd_req__abs_pump_activation`

**Step 0:** `arch` resolves directly to catalog key `arch`.

**Step 1:** routing table → `pharaoh-arch-draft` (architecture category).

**Step 2:** forward `parent_req_id`, `target_level=arch`, `element_description`.

**Step 3:** `pharaoh-arch-draft` returns its RST block for `arch__abs_pump_driver`.

**Step 4:** `gd_req__abs_pump_activation` lives in `docs/requirements/braking.rst`.
Suggested placement: `docs/requirements/architecture.rst`.

**Step 5 output (condensed):**

```
=== [ARTEFACT] arch: arch__abs_pump_driver ===
.. arch:: ABS pump driver component
   :id: arch__abs_pump_driver
   :status: draft
   :satisfies: gd_req__abs_pump_activation

   The ABS pump driver component manages the pump drive circuit, controlling
   output PWM duty cycle and providing over-current protection for the pump motor.

=== [AUTHORING SUMMARY] ===
{
  "need_id": "arch__abs_pump_driver",
  "type": "arch",
  "dispatched_skill": "pharaoh-arch-draft",
  "parent_link": "gd_req__abs_pump_activation",
  "file_placement": "docs/requirements/architecture.rst",
  "stop_reason": null
}
```

```
Consider running `pharaoh-verify arch__abs_pump_driver` to confirm the drafted
artefact addresses the substance of its parent.
```

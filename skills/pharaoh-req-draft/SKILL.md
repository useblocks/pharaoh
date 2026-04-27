---
name: pharaoh-req-draft
description: Use when drafting a single sphinx-needs requirement from a feature description. Produces a new RST directive block with ID, status=draft, and a single shall-clause body, linking to a parent requirement or workflow per the project's artefact-catalog.
chains_to: [pharaoh-req-review]
---

# pharaoh-req-draft

## When to use

Invoke when the user provides a feature description (1-5 sentences) and wants a single requirement authored at a specific level. Do NOT decompose multiple levels; do NOT review existing requirements; do NOT draft architecture — those are separate skills.

This skill produces exactly one requirement per invocation. If the user appears to want multiple requirements from a single feature description, draft only the most direct one and tell the user to re-invoke for any additional requirements.

## Inputs

- **feature_context** (from user): short prose describing the feature, target level, safety relevance
- **parent_link** (from user or inferred): ID of the parent requirement or workflow the new req satisfies
- **tailoring** (from `.pharaoh/project/` files):
  - `id-conventions.yaml` — prefix, separator, and ID regex for each artefact type
  - `artefact-catalog.yaml` — required and optional fields for the target type
  - `checklists/requirement.md` — ISO 26262-8 §6 axes used in self-check
- **needs.json** (built artefact index): used for parent resolution and ID uniqueness

> Note: A `shared/tailoring-access.md` helper module is planned. Until it exists, Steps 1-2 below
> inline the tailoring-access logic directly. When that file is created, this skill should be
> updated to delegate to it.

## Outputs

A single RST directive block matching the project's requirement prefix (e.g. `gd_req::` for Score), containing:

- Unique ID per id-conventions
- `:status: draft`
- `:satisfies:` link to parent_link (validated present in needs.json)
- `:verification:` link stub — use `tc__TBD` if no test ID exists yet; this is flagged in the output
- Single-sentence body with exactly one `shall`, no coordinating conjunctions within the shall clause
- No additional conjectural content beyond the single shall statement

---

## Process

### Step 1: Read tailoring

Read three files from `.pharaoh/project/`:

**1a. `id-conventions.yaml`**

Extract:
- `prefixes` — map of artefact-type key to description (e.g. `gd_req: requirement (guide-level)`)
- `separator` — string used between prefix and local-ID part (e.g. `__`)
- `id_regex` — regex pattern all generated IDs must match (e.g. `^[a-z][a-z_]*__[a-z0-9_]+$`)
- `id_regex_exceptions` — per-type overrides (note: `std_req` is exempt for Score)

Determine the correct prefix key for the requested requirement level. For Score, use `gd_req` for guide-level requirements. If the user specifies a different level, select the matching prefix from the `prefixes` map. If no matching prefix exists, FAIL:

```
FAIL: prefix for level "<level>" not found in id-conventions.yaml.
Available prefixes: <list>
```

**1b. `artefact-catalog.yaml`**

Read the entry for the resolved prefix key. Record:
- `required_fields` — every field that must appear in the directive
- `optional_fields` — fields that may appear
- `lifecycle` — valid values for `:status:`

Built-in default profile (bundled example): required = `[id, status, satisfies]`; optional = `[complies, tags, rationale, verification]`; lifecycle = `[draft, valid, inspected]`.

**1c. `checklists/requirement.md`**

Read the Individual checklist axes. These will be used in Step 6 self-check. You do not need to apply the Set-level axes at draft time. Record which axes are mechanically checkable at single-requirement level:
- `unambiguity` — one `shall`, no coordinating conjunctions in shall clause
- `atomicity` — body is a single shall statement
- `verifiability` — `:verification:` link present and non-empty

---

### Step 2: Locate and parse needs.json

Find `needs.json` in the project build directory. Common locations (check in order):
1. `docs/_build/needs/needs.json`
2. `_build/needs/needs.json`
3. Any `needs.json` under a `_build` directory

If not found, FAIL:

```
FAIL: needs.json not found. Build the Sphinx project first (`sphinx-build docs/ docs/_build/`),
then re-run this skill. needs.json is required for parent validation and ID uniqueness.
```

Parse the JSON. Extract:
- A flat map of `id → {id, type, status, ...}` across all needs
- The set of all existing IDs (for uniqueness check in Step 3)

---

### Step 3: Validate parent_link

The user must supply a `parent_link` — an ID of an existing requirement or workflow that the new requirement will satisfy.

1. Look up `parent_link` in the needs.json ID map.
2. If not found, FAIL:

```
FAIL: parent "<parent_link>" not found in needs.json.
Specify an existing parent ID. Available IDs starting with that prefix: <up to 5 examples>
```

3. If the parent is of an incompatible type (e.g. a `wp` artefact cannot be a `satisfies` target for `gd_req` in Score), warn but do not block — the user may be modeling a cross-type link intentionally.

4. If `parent_link` was not provided at all and cannot be inferred from context, FAIL:

```
FAIL: parent_link required. Provide the ID of the parent requirement or workflow
this new requirement satisfies.
```

---

### Step 4: Assign a unique ID

Generate a unique ID for the new requirement.

**4a. Determine the local-ID part**

The ID format is `<prefix><separator><local>`, e.g. `gd_req__brake_activation_threshold`.

Derive the local part from the feature_context:
- Lowercase, words separated by underscores
- Maximum 5 words; trim articles and prepositions
- Must satisfy `id_regex` after combining with prefix and separator
- Example: feature "Brake activation threshold at low speed" → local `brake_activation_threshold`

**4b. Check uniqueness**

Look up `<prefix><separator><local>` in the needs.json ID set. If it already exists, append a numeric suffix starting at `2`:
- `gd_req__brake_activation_threshold` taken → try `gd_req__brake_activation_threshold_2`, then `_3`, etc.

**4c. Validate against id_regex**

Confirm the final candidate matches `id_regex` (or the applicable `id_regex_exceptions` entry).
If it does not match, FAIL:

```
FAIL: generated ID "<id>" does not match id_regex "<regex>".
Revise the feature_context to use lowercase ASCII words.
```

---

### Step 5: Draft the requirement body

Write a single sentence that:

1. Uses exactly one `shall`
2. Names a subject (the system, component, or actor)
3. Specifies a condition or measurable criterion where the feature_context provides one
4. Contains no coordinating conjunctions (`and`, `or`, `but`) within the `shall` clause
5. Does not interpret or expand the feature_context beyond what is stated — if the context is too vague to write a specific shall clause, see Guardrails
6. Describes **observable behavior at the component boundary**, not internal mechanism. Do NOT name internal methods, classes, private variables, field names, or module-local symbols inside the shall body. External API names (published HTTP routes, CLI flags, pypi packages, protocol names, algorithm names) ARE observable and are fine. Rationale: the prior dogfooding audit showed ~7% (3/40) of LLM-drafted shall clauses named internal symbols AND got the described mechanism wrong — internal-name mentions rot on rename and are a primary accuracy-failure class. Keep traceability to internal symbols in `pharaoh-req-codelink-annotate` output, not in the shall body.

Good patterns:
- `The <system> shall <action> when <condition>.`
- `The <system> shall <action> within <measurable criterion>.`
- `The <component> shall <provide/reject/signal> <object> <constraint>.`
- `The exporter shall use HMAC-SHA256 to sign each outgoing request.` ← algorithm is observable at the boundary, fine to name.

Bad patterns (reject these in Step 6):
- Two verbs joined by `and`: `The system shall detect and report...` → FAIL
- Implicit plural: `The system shall check all sensors...` → acceptable only if "all" is intentional scope
- Vague quantity: `The system shall respond quickly` → too vague; note in output
- Internal symbol in the shall body: `The system shall use global_id to drive create-vs-update.` → internal variable name, will rot; rewrite as `The exporter shall decide create-vs-update based on whether a tracked identifier is already known for the need.`

---

### Step 6: Self-check

Before emitting, run these checks. If a check fails, attempt to re-draft (up to 2 retries). If still failing after 2 retries, emit the directive with a `[DIAGNOSTIC]` annotation explaining the issue.

**Check A — single shall**

Count occurrences of `shall` in the body. Must be exactly 1.

```python
assert body.count("shall") == 1
```

If `> 1`: split into the first shall clause and discard the rest. Re-draft a clean single-shall body.

**Check B — no conjunction in shall clause**

Extract the shall clause (text from `shall` to end of sentence). Check for `, and `, `, or `, ` and `, ` or ` within it.

If found: split into the primary action only. Re-draft.

**Check B.bis — no internal symbol in shall clause**

Flag any of the following patterns inside the shall body:
- An identifier in backticks (`` `foo_bar` ``) that is NOT one of the external-surface classes whitelisted for backticks: CLI flags (``--host``), env vars (``APP_LICENSE_KEY``), TOML config keys / section headers (``[myapp.export_config]``, ``links_delimiter``), protocol tokens (``HMAC-SHA256``), HTTP routes (``/itemtypes``). Internal function / method names, private variables, and implementation identifiers (`lower_snake` / `camelCase` symbols not in the whitelist) stay bare.
- A function-call shape like `some_func(...)` in the shall body.
- A private-looking variable reference (`self.x`, `obj._y`).

The whitelist mirrors `pharaoh-req-from-code` Rule 7. Project-internal TOML keys that never appear in public docs are still acceptable in backticks — a tester must copy-paste them verbatim — so do NOT require public-doc evidence on the whitelisted classes.

If found, re-draft to describe the observable behavior without naming the internal symbol (see Step 5 guideline 6). After 2 retries, emit with `[DIAGNOSTIC] shall body names internal symbol — post-emit revision required.`

**Check C — parent resolves**

Confirm `satisfies` ID is present in needs.json (already checked in Step 3, re-confirm before emit).

**Check D — ID unique**

Confirm chosen ID does not appear in needs.json (already checked in Step 4, re-confirm before emit).

**Check E — required fields present**

Verify the directive block includes every field from `required_fields` in artefact-catalog.yaml.
For the built-in default profile: `id`, `status`, `satisfies` must all be present.

---

### Step 7: Emit the directive block

Produce the final RST directive. Follow the exact format:

```rst
.. <prefix>:: <title>
   :id: <id>
   :status: draft
   :satisfies: <parent_link>
   :verification: <test_id or tc__TBD>

   <single-sentence body with exactly one shall>
```

Formatting rules:
- Directive line: `.. <prefix>:: <title>` with exactly one space after `..` and one space after `::`.
- Options: indented by 3 spaces. Format: `:<option>: <value>`.
- One blank line between options block and content body.
- Content body: indented by 3 spaces.
- One blank line after the content body.

If `:verification:` is set to `tc__TBD`, append a flagged note after the block:

```
[FLAG] :verification: set to tc__TBD — link to a real test case before promoting to status=valid.
```

Include optional fields only if the user explicitly provided values for them (e.g. rationale, tags). Do not invent optional field values.

---

## Guardrails

**G1 — Ambiguous level**

If feature_context describes behaviour at two distinct abstraction levels (e.g. component-level and unit-level) without the user specifying a target level, FAIL before drafting:

```
FAIL: context is ambiguous between level <X> and level <Y>.
Re-run with target_level specified (e.g. "component-level" or "unit-level").
```

**G2 — Parent not in needs.json**

If parent_link does not resolve in needs.json (as detected in Step 3), FAIL:

```
FAIL: parent "<parent_link>" not found in needs.json.
Specify an existing parent ID or build the project first.
```

**G3 — Multiple shall after 2 retries**

If the drafted body still contains `> 1 shall` or a conjunction in the shall clause after 2 self-correction attempts, emit the directive as-is with a diagnostic:

```
[DIAGNOSTIC] Body failed shall-atomicity check after 2 retries.
Issue: <check A or B description>
Action required: manually edit the body before review.
```

Do not block the user — emit with the diagnostic so they can proceed and fix manually.

**G4 — Feature context too vague**

If feature_context does not contain enough specifics to write a measurable shall clause (no actor, no action, no condition), FAIL and ask for more detail:

```
FAIL: feature_context is too vague to draft a verifiable requirement.
Please provide: (1) the system/component subject, (2) the required action or property,
(3) any measurable condition or threshold.
```

---

## Advisory chain

After successfully emitting the directive, always advise:

```
Consider running `pharaoh-req-review <new_id>` to audit against ISO 26262-8 §6 axes.
```

Do not show this if the emit included a `[DIAGNOSTIC]` (the user has a more urgent issue to fix first).

---

## Worked example

**Feature context (user input):**
> "The brake controller shall engage the ABS pump when wheel slip exceeds a calibrated threshold. Target level: component. Parent: gd_req__brake_system_safety"

**Step 1 result:** prefix = `gd_req`, separator = `__`, id_regex = `^[a-z][a-z_]*__[a-z0-9_]+$`, required = `[id, status, satisfies]`, optional includes `verification`.

**Step 2 result:** needs.json found at `docs/_build/needs/needs.json`; 185 IDs loaded.

**Step 3 result:** `gd_req__brake_system_safety` found in needs.json. Parent valid.

**Step 4 result:** local = `abs_pump_activation`; candidate = `gd_req__abs_pump_activation`; not in needs.json; passes id_regex. ID assigned.

**Step 5 draft body:**
> The brake controller shall engage the ABS pump when measured wheel slip exceeds the calibrated activation threshold.

**Step 6 checks:** `shall` count = 1 ✓; no conjunction in shall clause ✓; parent resolves ✓; ID unique ✓; required fields all present ✓.

**Step 7 output:**

```rst
.. gd_req:: ABS pump activation on wheel slip threshold
   :id: gd_req__abs_pump_activation
   :status: draft
   :satisfies: gd_req__brake_system_safety
   :verification: tc__TBD

   The brake controller shall engage the ABS pump when measured wheel slip exceeds
   the calibrated activation threshold.
```

```
[FLAG] :verification: set to tc__TBD — link to a real test case before promoting to status=valid.

Consider running `pharaoh-req-review gd_req__abs_pump_activation` to audit against ISO 26262-8 §6 axes.
```

## Last step

After emitting the artefact, invoke `pharaoh-req-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must regenerate (via `pharaoh-req-regenerate` if available, or by re-invoking this skill with the findings as input).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

---
name: pharaoh-req-draft
description: Use when drafting a single sphinx-needs requirement-shaped artefact (req, comp_req, sysreq, swreq, hazard, safety_goal, fsr, etc.) from a feature description. The artefact type is parameterised via `target_level` (any catalog-declared requirement-shaped type — including ISO 26262 safety-V types). Produces a new RST directive block with ID, status=draft, and either a shall-clause body (requirement-shaped) or a hazard/goal-shaped body, linking to a parent per the project's artefact-catalog.
chains_to: [pharaoh-req-review]
---

# pharaoh-req-draft

## When to use

Invoke when the user provides a short feature, hazard, or safety-goal description (1-5 sentences) and wants a single requirement-shaped artefact authored at a specific catalog-declared level. Do NOT decompose multiple levels; do NOT review existing artefacts; do NOT draft architecture — those are separate skills.

This skill produces exactly one artefact per invocation. If the user appears to want multiple artefacts from a single description, draft only the most direct one and tell the user to re-invoke for any additional ones.

This skill is the canonical drafter for any requirement-shaped type the project's
`artefact-catalog.yaml` declares — classical levels (`req`, `comp_req`, `sysreq`, `swreq`,
`gd_req`) as well as ISO 26262 safety-V types (`hazard` for HARA outputs, `safety_goal`
for Part 3 goals, `fsr` for Part 4 functional safety requirements, `tsr` for Part 4
technical safety requirements). The skill drives every type from the catalog's
`required_fields` and `required_metadata_fields`; nothing in the skill is hardcoded to a
fixed allow-list of types.

### ISO 26262 framing

Safety-V types follow ISO 26262 Part 3 (HARA → safety goals) and Part 4 (FSR / TSR)
flow. This skill is not a safety expert system: it does not decide ASIL ratings or
hazard classifications. It surfaces the ISO-26262-relevant fields (`asil`, `severity`,
`exposure`, `controllability`, `safe_state`, etc.) as placeholders when the project's
catalog declares them required, and prompts the user to fill them. Projects that do
not declare these fields in their catalog get a plain requirement; projects that do
(e.g. `useblocks/sphinx-needs-demo` with a HARA tailoring) get the safety-V shape.

## Inputs

- **feature_context** (from user): short prose describing the feature, hazard, or safety
  goal — plus the safety relevance if any
- **target_level** (from user): the artefact-catalog type name to emit. Any type declared
  in `.pharaoh/project/artefact-catalog.yaml` is accepted, including:
  - classical requirement levels — `req`, `comp_req`, `sysreq`, `swreq`, `gd_req`, …
  - ISO 26262 safety-V types — `hazard`, `safety_goal`, `fsr`, `tsr`, …
  The emitted directive uses `target_level` verbatim as the directive name; the ID prefix,
  required fields, and required metadata fields are resolved from the catalog and
  `id-conventions.yaml`. If `target_level` is absent the skill falls back to the project's
  primary requirement type (`gd_req` in Score, `req` in the bundled defaults) — pass it
  explicitly when drafting safety-V artefacts.
- **parent_link** (from user or inferred): ID of the parent the new artefact links to
  via the catalog-declared link relation (`:satisfies:` for classical reqs and FSRs,
  `:safety_goal_for:` / `:derives_from:` / similar for safety-V — read from the catalog).
- **safety_classification** (optional, from user): metadata block for ASIL-related fields
  on safety-V types. Recommended (but not required) when `target_level` is one of
  `hazard`, `safety_goal`, `fsr`, or `tsr`. Common shape:
  `{asil: "B", severity: "S2", exposure: "E3", controllability: "C2", safe_state: "..."}`.
  Each field is emitted only if the catalog declares it as `required_fields` or
  `required_metadata_fields`; surplus fields are dropped silently. Missing values for
  catalog-required fields are emitted as `<TBD>` placeholders with a `[FLAG]` line so the
  user knows to fill them.
- **tailoring** (from `.pharaoh/project/` files):
  - `id-conventions.yaml` — prefix, separator, and ID regex for each artefact type
  - `artefact-catalog.yaml` — `required_fields`, `optional_fields`, `required_metadata_fields`,
    `required_links`, `lifecycle` for the target type
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

**1a. `artefact-catalog.yaml`**

Resolve `target_level` against the catalog. Look up the entry whose top-level key equals
`target_level`. If found, record:

- `required_fields` — every field that must appear in the directive (e.g. `id`, `status`,
  `satisfies` for a classical req; plus `asil`, `severity`, `exposure`,
  `controllability`, `safe_state` for safety-V types when the catalog declares them)
- `optional_fields` — fields that may appear
- `required_metadata_fields` — option keys that must be set with non-empty values before
  release. Treated as required at draft time too — any missing value is emitted as `<TBD>`
  with a `[FLAG]` line.
- `required_links` — link-relation names that every artefact of this type must declare
  with a non-empty target list (e.g. `satisfies` for a comp_req, `safety_goal_for` for
  an `fsr`, `derives_from` for a `safety_goal`). Use this to pick the right link option
  in Step 7 — never hardcode `:satisfies:`.
- `lifecycle` — valid values for `:status:`

If the entry is absent, FAIL:

```
FAIL: target_level "<value>" is not declared in .pharaoh/project/artefact-catalog.yaml.
Add an entry for "<value>" (with required_fields, optional_fields, lifecycle, and any
required_metadata_fields / required_links) before drafting, or pass a target_level that
is already declared.
```

If `target_level` was not provided by the caller, fall back to the project's primary
requirement type — the first catalog key whose suffix is `req` (e.g. `gd_req` in Score,
`req` in the bundled defaults) — and note the fallback in the output. Always pass
`target_level` explicitly when drafting safety-V types (`hazard`, `safety_goal`, `fsr`,
`tsr`); the fallback is only safe for classical requirements.

Built-in default profile (bundled example, used when no catalog is present): `req` with
required = `[id, status, satisfies]`; optional = `[complies, tags, rationale, verification]`;
lifecycle = `[draft, valid, inspected]`.

**1b. `id-conventions.yaml`**

Extract:
- `prefixes` — map of artefact-type key to its identifier prefix string. Read the value
  for `target_level`.
- `separator` — string used between prefix and local-ID part (e.g. `__`)
- `id_regex` — regex pattern all generated IDs must match (e.g. `^[a-z][a-z_]*__[a-z0-9_]+$`)
- `id_regex_exceptions` — per-type overrides (note: `std_req` is exempt for Score)

If `prefixes` does not declare `target_level`, FAIL:

```
FAIL: id-conventions.yaml prefixes map has no entry for "<target_level>".
Declare a prefix for "<target_level>" before drafting.
```

**1c. `checklists/requirement.md`**

Read the Individual checklist axes. These will be used in Step 6 self-check. You do not need to apply the Set-level axes at draft time. Record which axes are mechanically checkable at single-artefact level:
- `unambiguity` — one `shall`, no coordinating conjunctions in shall clause (applies to
  shall-clause types — `req`, `fsr`, `tsr`, `safety_goal`)
- `atomicity` — body is a single shall statement (or a single hazard statement for
  `hazard` types — see Step 5)
- `verifiability` — `:verification:` link present and non-empty (where the catalog declares it)

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

### Step 5: Draft the body

Body shape depends on `target_level`:

- **Shall-clause types** — `req`, `comp_req`, `sysreq`, `swreq`, `gd_req`, `fsr`, `tsr`,
  `safety_goal` (and any catalog type whose checklist declares the unambiguity / atomicity
  shall axes): write a single shall sentence per the rules below.
- **Hazard types** — `hazard` (and any catalog type that documents an event/situation rather
  than a behaviour): write a single declarative sentence describing the hazardous event,
  its trigger condition, and the affected vehicle/actor — NO `shall`. Example:
  `Unintended ABS pump activation while driving on dry asphalt at >80 km/h causes loss of
  braking force on the front axle.` Then rely on the catalog's `required_metadata_fields`
  (severity / exposure / controllability / asil) to carry the HARA classification — do
  NOT bake those values into the body prose.

For a **shall-clause** body, write a single sentence that:

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

**Check A — single shall (shall-clause types only)**

For shall-clause types, count occurrences of `shall` in the body. Must be exactly 1.

```python
assert body.count("shall") == 1
```

If `> 1`: split into the first shall clause and discard the rest. Re-draft a clean single-shall body.

For hazard types, skip this check — body must NOT contain `shall`. If `shall` appears in
a hazard body, re-draft the hazard as a declarative event statement.

**Check B — no conjunction in shall clause (shall-clause types only)**

For shall-clause types, extract the shall clause (text from `shall` to end of sentence).
Check for `, and `, `, or `, ` and `, ` or ` within it.

If found: split into the primary action only. Re-draft.

For hazard types, skip this check — a single hazard sentence may legitimately combine a
trigger condition and an effect (`while driving on dry asphalt and braking…`).

**Check B.bis — no internal symbol in shall clause**

Flag any of the following patterns inside the shall body:
- An identifier in backticks (`` `foo_bar` ``) that is NOT one of the external-surface classes whitelisted for backticks: CLI flags (``--host``), env vars (``APP_LICENSE_KEY``), TOML config keys / section headers (``[myapp.export_config]``, ``links_delimiter``), protocol tokens (``HMAC-SHA256``), HTTP routes (``/itemtypes``). Internal function / method names, private variables, and implementation identifiers (`lower_snake` / `camelCase` symbols not in the whitelist) stay bare.
- A function-call shape like `some_func(...)` in the shall body.
- A private-looking variable reference (`self.x`, `obj._y`).

The whitelist mirrors `pharaoh-req-from-code` Rule 7. Project-internal TOML keys that never appear in public docs are still acceptable in backticks — a tester must copy-paste them verbatim — so do NOT require public-doc evidence on the whitelisted classes.

If found, re-draft to describe the observable behavior without naming the internal symbol (see Step 5 guideline 6). After 2 retries, emit with `[DIAGNOSTIC] shall body names internal symbol — post-emit revision required.`

**Check C — parent resolves**

Confirm the parent ID under the catalog-declared link relation (`:satisfies:` for classical
reqs, `:safety_goal_for:` / `:derives_from:` / similar per the catalog's `required_links`
for safety-V types) is present in needs.json (already checked in Step 3, re-confirm before
emit).

**Check D — ID unique**

Confirm chosen ID does not appear in needs.json (already checked in Step 4, re-confirm before emit).

**Check E — required fields present**

Verify the directive block includes every field from `required_fields` in
`artefact-catalog.yaml`. For the bundled default profile: `id`, `status`, `satisfies` must
all be present. For a safety-V type whose catalog entry declares e.g.
`required_fields: [id, status, safety_goal_for, asil, severity, exposure, controllability]`,
every one of those options must appear (use `<TBD>` placeholder when the user did not
supply a value, and emit a `[FLAG]` line per placeholder).

**Check F — required metadata fields present**

For each entry in `required_metadata_fields` from the catalog, confirm the directive
emits the option with a non-empty value or a `<TBD>` placeholder. Emit a `[FLAG]` line
for every `<TBD>` so the user knows release will block until it is filled.

---

### Step 7: Emit the directive block

Produce the final RST directive. Use `target_level` verbatim as the directive name.
Emit every option from `required_fields` (with values supplied by the user or `<TBD>`
placeholders), every link in `required_links` (with the user-supplied parent ID), and
every option in `required_metadata_fields` (value or `<TBD>`):

```rst
.. <target_level>:: <title>
   :id: <id>
   :status: draft
   :<required_link_relation>: <parent_link>
   <... every other field from required_fields ...>
   <... every option from required_metadata_fields ...>

   <body per Step 5 — single shall for shall-clause types, declarative event for hazards>
```

Formatting rules:
- Directive line: `.. <target_level>:: <title>` with exactly one space after `..` and one space after `::`.
- Options: indented by 3 spaces. Format: `:<option>: <value>`.
- One blank line between options block and content body.
- Content body: indented by 3 spaces.
- One blank line after the content body.

If `:verification:` (or any other field) is set to `<TBD>`, append a flagged note per
placeholder after the block:

```
[FLAG] :verification: set to tc__TBD — link to a real test case before promoting to status=valid.
[FLAG] :asil: set to <TBD> — assign an ASIL level (A/B/C/D/QM) before release.
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

## Worked examples

### Example 1 — classical guide-level requirement (Score)

**Feature context (user input):**
> "The brake controller shall engage the ABS pump when wheel slip exceeds a calibrated
> threshold. target_level: gd_req. Parent: gd_req__brake_system_safety"

**Step 1 result:** catalog entry `gd_req` has `required_fields: [id, status, satisfies]`,
`required_links: [satisfies]`, optional includes `verification`. id-conventions prefix
`gd_req`, separator `__`, id_regex `^[a-z][a-z_]*__[a-z0-9_]+$`.

**Step 2 result:** needs.json found at `docs/_build/needs/needs.json`; 185 IDs loaded.

**Step 3 result:** `gd_req__brake_system_safety` found in needs.json. Parent valid.

**Step 4 result:** local = `abs_pump_activation`; candidate = `gd_req__abs_pump_activation`; not in needs.json; passes id_regex. ID assigned.

**Step 5 draft body** (shall-clause type):
> The brake controller shall engage the ABS pump when measured wheel slip exceeds the calibrated activation threshold.

**Step 6 checks:** `shall` count = 1 ✓; no conjunction in shall clause ✓; parent resolves ✓; ID unique ✓; required fields all present ✓; no `required_metadata_fields` declared.

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

### Example 2 — ISO 26262 functional safety requirement (FSR)

**Feature context (user input):**
> "The braking ECU shall command vehicle deceleration to a defined safe state within
> 100 ms of detecting unintended ABS pump activation. target_level: fsr.
> Parent (the safety goal it implements): sg__no_unintended_abs_pump_activation."
>
> safety_classification: `{asil: "B", safe_state: "wheels_unlocked_no_abs_modulation"}`

**Step 1 result:** catalog entry for `fsr` declares
`required_fields: [id, status, safety_goal_for, asil, safe_state]`,
`required_links: [safety_goal_for]`, `required_metadata_fields: [asil, safe_state]`,
`lifecycle: [draft, reviewed, approved]`. id-conventions prefix `fsr`, separator `__`.

**Step 2 result:** needs.json found at `docs/_build/needs/needs.json`; 240 IDs loaded.

**Step 3 result:** `sg__no_unintended_abs_pump_activation` found in needs.json (type
`safety_goal`). Catalog-declared link relation for `fsr` is `safety_goal_for` (not
`satisfies`) — the skill uses that key, not a hardcoded `:satisfies:`.

**Step 4 result:** local = `safe_deceleration_on_unintended_pump`; candidate =
`fsr__safe_deceleration_on_unintended_pump`; passes id_regex. ID assigned.

**Step 5 draft body** (shall-clause type — `fsr` is a requirement-shaped safety-V type):
> The braking ECU shall command vehicle deceleration to the
> `wheels_unlocked_no_abs_modulation` safe state within 100 ms of detecting unintended
> ABS pump activation.

**Step 6 checks:** `shall` count = 1 ✓; no conjunction ✓; parent resolves ✓; ID unique ✓;
required fields `[id, status, safety_goal_for, asil, safe_state]` all present (asil and
safe_state from `safety_classification`) ✓; required_metadata_fields `[asil, safe_state]`
both non-empty ✓.

**Step 7 output:**

```rst
.. fsr:: Safe deceleration on unintended ABS pump activation
   :id: fsr__safe_deceleration_on_unintended_pump
   :status: draft
   :safety_goal_for: sg__no_unintended_abs_pump_activation
   :asil: B
   :safe_state: wheels_unlocked_no_abs_modulation

   The braking ECU shall command vehicle deceleration to the
   wheels_unlocked_no_abs_modulation safe state within 100 ms of detecting
   unintended ABS pump activation.
```

```
Consider running `pharaoh-req-review fsr__safe_deceleration_on_unintended_pump` to audit
against ISO 26262-8 §6 axes (the same checklist applies to FSRs as to classical reqs).
```

For a hazard-typed draft (`target_level: hazard`), the catalog typically declares
`required_metadata_fields: [severity, exposure, controllability, asil]`. The skill emits
those options as `<TBD>` placeholders when `safety_classification` does not include
them, and the body is a single declarative event sentence (no `shall`) — see Step 5.

## Last step

After emitting the artefact, invoke `pharaoh-req-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`. If the review emits any axis with `score: 0` or `severity: critical`, return a non-success status with the review findings verbatim and do NOT finalize the artefact — the caller must regenerate (via `pharaoh-req-regenerate` if available, or by re-invoking this skill with the findings as input).

See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism. Coverage is mechanically enforced by `pharaoh-self-review-coverage-check` in `pharaoh-quality-gate`.

---
name: pharaoh-req-regenerate
description: Use when regenerating a single sphinx-needs requirement to address findings from pharaoh-req-review. Consumes the original RST + findings JSON, emits a revised RST directive that passes the flagged axes.
chains_from: [pharaoh-req-review]
chains_to: [pharaoh-req-review]
---

# pharaoh-req-regenerate

## When to use

Invoke when `pharaoh-req-review` has produced a findings JSON for a single requirement and
`overall` is `"needs_work"` or `"fail"`. Provide the original RST directive block and the
findings JSON together.

Do NOT use to re-author a requirement from scratch — use `pharaoh-req-draft` for new requirements.
Do NOT invoke when `overall` is `"pass"` and no subjective axis scored below 2 (see Guardrail G2).
One invocation addresses one requirement. If multiple requirements need regeneration, run this
skill once per requirement.

---

## Inputs

- **original_rst** (from user): the RST directive block produced by `pharaoh-req-draft` or
  retrieved from needs.json — must include the `:id:` option
- **findings_json** (from `pharaoh-req-review`): the full structured findings JSON for that
  requirement — must contain the `axes` and `action_items` fields
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — required/optional fields for the target artefact type
  - `id-conventions.yaml` — id_regex for output validation
  - `checklists/requirement.md` — axis definitions for self-check
- **needs.json**: used to confirm the re-issued need-id is still unique and parent links resolve

> Note: A `shared/tailoring-access.md` helper module is planned. Until it exists, Steps 1-2 below
> inline the tailoring-access logic directly. When that file is created, this skill should be
> updated to delegate to it.

---

## Outputs

A single revised RST directive block where every failing binary axis now passes and every
subjective axis that scored < 2 has been reworded to score ≥ 2.

Preserved fields (must not change unless the review explicitly flagged them):
- `:id:` — never change the need-id
- `:status:` — preserve unless the `action_items` list contains an explicit status demotion
- `:satisfies:` — preserve the parent link

If the review flagged a missing required field (schema axis), add the field with a best-effort
value and append a `[FLAG]` note identifying it.

---

## Process

### Step 1: Read tailoring

Read `.pharaoh/project/artefact-catalog.yaml` and `.pharaoh/project/id-conventions.yaml`.

Extract for the artefact type matching the directive prefix (e.g. `gd_req`):
- `required_fields` — every field that must be present
- `id_regex` — regex the output id must match

If tailoring files are missing, fall back to built-in defaults (bundled example
requirement profile — `req` required: `[id, status, satisfies]`, id_regex:
`^[a-z][a-z_]*__[a-z0-9_]+$`).

---

### Step 2: Parse findings_json

Parse the findings JSON. If malformed (missing `axes` key, invalid JSON syntax, axis count < 11),
FAIL immediately — do not attempt partial regeneration:

```
FAIL: findings_json is malformed — <specific parse error>.
Re-run `pharaoh-req-review` on the requirement to obtain a valid findings JSON,
then re-invoke pharaoh-req-regenerate with the corrected output.
```

Extract:
- `need_id` — must match the `:id:` in original_rst; if mismatched, FAIL:
  ```
  FAIL: findings_json.need_id "<a>" does not match original_rst :id: "<b>".
  Supply matching RST and findings for the same requirement.
  ```
- `axes` — a map of axis → `{score, reason}` entries
- `action_items` — the list of strings describing required changes

---

### Step 3: Identify axes to fix

For each axis in `axes`:

- Binary axis (score is 0 or 1): mark for fix if `score == 0`
- Subjective axis (score is 0–3): mark for fix if `score < 2`
- Deferred axis (score == "deferred") or null axis: skip — not fixable at single-req scope

Build a prioritised fix list:
1. Binary failures first (blocking for `overall = "fail"`)
2. Subjective axes scoring 0 or 1 second

---

### Step 4: Apply fixes

Work through the fix list. For each axis:

**atomicity / unambiguity_prose** (body contains > 1 `shall` or a conjunction in the shall clause):

Read the original body. Identify the primary action. Discard secondary clauses. Rewrite as a
single `shall` sentence with no `, and`/`, or`/` and `/` or ` within the shall clause.
Preserve subject and measurable condition.

**verifiability** (`:verification:` absent or does not resolve):

If `:verification:` is absent: add `:verification: tc__TBD`.
If it is present but does not resolve: replace with `:verification: tc__TBD`.
Append `[FLAG] :verification: set to tc__TBD — link to a real test case before promoting to status=valid.`

**schema** (required field missing):

Add the missing field. If the value cannot be inferred from context, use a placeholder:
- `:satisfies:` missing: set to `TBD` and append `[FLAG] :satisfies: requires a real parent ID.`
- Other missing fields: add empty with `[FLAG]`.

**unambiguity_prose** (score < 2, no shall-atomicity failure):

Replace vague quantifiers (e.g. "sufficient", "quickly", "within a reasonable time") with
either a concrete criterion (if the original_rst or user context supplies one) or a clearly
labelled parameter placeholder: `<THRESHOLD_TO_BE_DEFINED>`.

**comprehensibility** (score < 2):

Expand the subject if missing or ambiguous. Remove undefined acronyms or expand them inline
on first use. Do not change the measurable claim.

**feasibility** (score < 2):

Add or tighten the constraint. If the claim is infeasible as stated, insert a
`[DIAGNOSTIC]` note asking the user to verify the feasibility constraint before re-reviewing.
Do not silently drop the constraint.

---

### Step 5: Self-check

After rewriting, run the same checks as `pharaoh-req-review` Step 3 (binary axes only):

- Atomicity: exactly one `shall`, no conjunction in shall clause
- Internal consistency: no self-contradiction
- Schema: all required fields present and non-empty
- Verifiability: `:verification:` present. On a `status: draft` requirement, a placeholder value matching `^(tc|test_case)__TBD$` (or the project's `tailoring.verification_placeholder_regex`) scores 0.5 on review's verifiability axis — passing the binary gate and terminating the regen loop. Once status advances past draft, the placeholder stops passing and a real test-case id is required.

If any binary check still fails after one rewrite attempt, attempt one further rewrite targeting
only the still-failing axis. If it still fails after two total attempts, emit the directive with:

```
[DIAGNOSTIC] axis "<name>" still failing after 2 rewrite attempts.
Manual correction required before re-running pharaoh-req-review.
```

---

### Step 6: Fixed-point protection

If the revised directive is character-for-character identical to `original_rst`, the findings
indicated no change was needed or the rewrite is stuck. Stop and emit:

```
[DIAGNOSTIC] Regenerated output is identical to input after applying all fixes.
This may indicate the action_items are non-actionable at single-requirement scope
or that the findings_json and original_rst describe different requirements.
Review action_items manually.
```

Do not loop. Emit the original directive unchanged alongside the diagnostic.

---

### Step 7: Emit the revised directive

Emit the revised RST block using the same formatting rules as `pharaoh-req-draft`:

```rst
.. <prefix>:: <title>
   :id: <id>
   :status: <status>
   :satisfies: <parent_link>
   :verification: <test_id>

   <revised single-sentence body>
```

Followed by any `[FLAG]` or `[DIAGNOSTIC]` notes as plain text after the block.

---

## Guardrails

**G1 — Malformed findings_json**

If findings_json cannot be parsed or is missing required keys (`axes`, `action_items`):

```
FAIL: findings_json is malformed — <error>.
Re-run `pharaoh-req-review` to regenerate valid findings, then retry.
```

**G2 — No action required**

If the findings_json reports `overall = "pass"` AND no subjective axis scores below 2:

```
NO-OP: findings_json overall = "pass" with all subjective axes ≥ 2.
This requirement already passes all evaluated axes. No regeneration needed.
```

Return this message only, without emitting a directive.

**G3 — Fixed-point loop protection**

If two sequential invocations produce the same output (caller detects this externally and passes
the same `original_rst` and `findings_json` again without change), emit:

```
[DIAGNOSTIC] Fixed-point detected: same input and same output on consecutive invocations.
Axes that cannot be resolved at single-requirement scope: <list>.
Escalate to manual authoring or review with a human expert.
```

---

## Advisory chain

After successfully emitting the revised directive:

```
Consider running `pharaoh-req-review <need_id>` to confirm all axes now pass.
```

Do not show this if the emit included a `[DIAGNOSTIC]`.

---

## Worked example

**Original RST (from pharaoh-req-draft):**

```rst
.. gd_req:: Brake pressure limit check
   :id: gd_req__brake_pressure_limit
   :status: draft
   :satisfies: gd_req__brake_system_safety

   The brake controller shall detect excessive pressure and activate the pressure relief
   valve and log the event.
```

**Findings JSON (from pharaoh-req-review):**

```json
{
  "need_id": "gd_req__brake_pressure_limit",
  "axes": {
    "atomicity":            {"score": 0, "reason": "conjunction 'and' joins two actions within the shall clause"},
    "internal_consistency": {"score": 1, "reason": "no self-contradiction"},
    "verifiability":        {"score": 0, "reason": ":verification: field absent"},
    "schema":               {"score": 1, "reason": "id, status, satisfies present"},
    "completeness":         {"score": "deferred", "reason": "set-level axis"},
    "external_consistency": {"score": "deferred", "reason": "set-level axis"},
    "no_duplication":       {"score": "deferred", "reason": "set-level axis"},
    "maintainability":      {"score": null, "reason": "chain-level axis"},
    "unambiguity_prose":    {"score": 2, "reason": "mostly clear; slight scope ambiguity from compound action"},
    "comprehensibility":    {"score": 3, "reason": "subject, action, condition all explicit"},
    "feasibility":          {"score": 3, "reason": "standard automotive function"}
  },
  "action_items": [
    "atomicity: split into one requirement — retain only the pressure relief valve activation; draft a separate requirement for event logging",
    "verifiability: add :verification: field"
  ],
  "overall": "fail"
}
```

**Step 3:** Axes to fix — atomicity (binary, score 0), verifiability (binary, score 0).

**Step 4 fixes:**
- atomicity: retain primary action (activate pressure relief valve); drop secondary clause (log the event).
  Body: "The brake controller shall activate the pressure relief valve when detected brake line pressure exceeds the maximum safe operating limit."
- verifiability: add `:verification: tc__TBD`.

**Step 5 self-check:** `shall` count = 1, no conjunction, required fields present, `:verification:` present. All binary axes pass.

**Step 6:** Output differs from input. No fixed-point.

**Step 7 output:**

```rst
.. gd_req:: Brake pressure limit check
   :id: gd_req__brake_pressure_limit
   :status: draft
   :satisfies: gd_req__brake_system_safety
   :verification: tc__TBD

   The brake controller shall activate the pressure relief valve when detected brake
   line pressure exceeds the maximum safe operating limit.
```

```
[FLAG] :verification: set to tc__TBD — link to a real test case before promoting to status=valid.

Consider running `pharaoh-req-review gd_req__brake_pressure_limit` to confirm all axes now pass.
```

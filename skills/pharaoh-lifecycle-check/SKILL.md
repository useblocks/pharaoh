---
name: pharaoh-lifecycle-check
description: Use when verifying a sphinx-needs artefact's current lifecycle state and the legality of a requested state transition per the project's workflows.yaml state machine.
chains_to: []
---

# pharaoh-lifecycle-check

## When to use

Invoke when you want to check whether a proposed state transition is allowed for a given need,
or to audit a need's current state against the state machine.

This skill is a deterministic state-machine check — no LLM judgment. It reads the project's
`workflows.yaml` and evaluates legality mechanically.

Do NOT invoke to change state — this skill only checks. Do NOT invoke for bulk transition
checks — one need per invocation.

---

## Inputs

- **need_id** (from user): ID of the need to check — must exist in `needs.json`
- **target_state** (from user, optional): the desired target state. If omitted, the skill
  audits the current state only (checks it is a valid declared state, no illegal prerequisites
  outstanding)
- **tailoring** (from `.pharaoh/project/`):
  - `workflows.yaml` — lifecycle state machine (states + transitions with `requires:` lists)
  - `artefact-catalog.yaml` — maps artefact type to lifecycle list
- **needs.json**: required to look up the need's current status and type

---

## Outputs

A single JSON document — no prose wrapper. Shape:

```json
{
  "need_id": "gd_req__abs_pump_activation",
  "artefact_type": "gd_req",
  "current_state": "draft",
  "target_state": "valid",
  "legal": true,
  "missing_prerequisites": [],
  "transition_path": ["draft", "valid"],
  "notes": []
}
```

Fields:
- `legal`: `true` if the transition is permitted per `workflows.yaml`; `false` otherwise
- `missing_prerequisites`: list of requirement strings from the `requires:` list that cannot
  be confirmed met from the need's current data (e.g. `"independent_review_complete"`)
- `transition_path`: ordered list of states from current to target (direct or multi-hop
  shortest path); `null` if unreachable
- `notes`: informational observations (e.g. current state not declared, indirect path needed)

If `target_state` was omitted, `target_state` is `null` and `legal` reflects whether the
current state is a valid declared state for this artefact type.

---

## Process

### Step 1: Load tailoring and needs.json

**1a.** Read `workflows.yaml` from `.pharaoh/project/`. Extract:
- `lifecycle_states` map (keys are valid state names)
- `transitions` list: each entry has `from`, `to`, `requires`

**1b.** Read `artefact-catalog.yaml`. Find the entry for the artefact type of `need_id`.
Record the `lifecycle` list for that type (if present).

**1c.** Find and parse `needs.json` (search order: `docs/_build/needs/needs.json`,
`_build/needs/needs.json`, any `needs.json` under `_build`). Extract the flat ID map.

If any required file is missing, FAIL with the missing-file path and a hint to rebuild or
run `pharaoh-tailor-fill`.

---

### Step 2: Resolve need

Look up `need_id` in the needs.json ID map. If not found, FAIL:

```
FAIL: need_id "<id>" not found in needs.json.
Verify the ID or rebuild the project.
```

Extract:
- `type` (artefact type, e.g. `gd_req`)
- `status` (current lifecycle state)

---

### Step 3: Validate current state

Check whether `status` (current state) is declared in `workflows.yaml.lifecycle_states`.

If not declared:
- Set `legal: false`
- Add to `notes`: `"Current state '<status>' is not declared in workflows.yaml lifecycle_states"`
- If `target_state` was not requested, emit result and stop.

If declared, current state is valid.

---

### Step 4: Check target state (if provided)

If `target_state` was not provided, emit with `target_state: null`, `legal: true`
(assuming current state is valid), and stop.

If `target_state` is provided:

**4a.** Confirm `target_state` is declared in `workflows.yaml.lifecycle_states`. If not:
- Set `legal: false`
- Add to `notes`: `"Target state '<target_state>' is not declared in workflows.yaml lifecycle_states"`
- Emit and stop.

**4b.** Build the transition graph from `workflows.yaml.transitions`. Find the shortest path
from `current_state` to `target_state` using BFS.

If no path exists:
- Set `legal: false`
- Set `transition_path: null`
- Add to `notes`: `"No transition path from '<current_state>' to '<target_state>' in workflows.yaml"`

If a path exists, set `transition_path` to the ordered list of states.

---

### Step 5: Check prerequisites

For each transition in the found path, read the `requires:` list. For each requirement string
in `requires:`:

- Check whether the requirement can be confirmed met from the need's current data. The
  following heuristics apply:
  - `"independent_review_complete"` — check whether the need has a `:reviewed_by:` or
    `:inspection_record:` field with a non-empty value in needs.json. If not present,
    mark as missing.
  - `"inspection_record_present"` — check whether the need has an `:inspection_record:` field
    with a non-empty value. If not present, mark as missing.
  - Any other requirement string — cannot be automatically confirmed; mark as missing with a
    note that manual verification is required.

Populate `missing_prerequisites` with strings that are not confirmed met.

If `missing_prerequisites` is non-empty, set `legal: false`.
If all prerequisites are met (or the `requires:` lists are empty), `legal` remains `true`.

---

### Step 6: Emit JSON

Emit the single JSON document. No prose before or after.

---

## Guardrails

**G1 — need_id not in needs.json**

FAIL immediately (Step 2). Do not proceed with guessed data.

**G2 — workflows.yaml missing**

If `workflows.yaml` is absent from `.pharaoh/project/`, FAIL:

```
FAIL: workflows.yaml not found at .pharaoh/project/workflows.yaml.
Run pharaoh-tailor-fill to generate tailoring files.
```

**G3 — Current state not declared**

Proceed but set `legal: false` and note the anomaly (Step 3). Do not abort — the output is
still useful for diagnosing the state machine gap.

---

## Advisory chain

No downstream chain. If `legal: false`, append after the JSON:

```
Resolve missing prerequisites or fix the state declaration before performing the transition.
```

---

## Worked example

**User input:**
- `need_id`: `gd_req__abs_pump_activation`
- `target_state`: `valid`

**Step 1:** `workflows.yaml` loaded. States: `draft`, `valid`, `inspected`. Transitions:
`draft → valid` (requires: `independent_review_complete`), `valid → inspected`
(requires: `inspection_record_present`), `inspected → draft` (requires: `[]`).

**Step 2:** Need found in needs.json. `type = gd_req`, `status = draft`.

**Step 3:** `draft` is declared in lifecycle_states. Current state valid.

**Step 4a:** `valid` declared. Continue.

**Step 4b:** BFS finds direct path `[draft, valid]`.

**Step 5:** Transition `draft → valid` requires `independent_review_complete`. The need has no
`:reviewed_by:` or `:inspection_record:` field in needs.json → prerequisite unconfirmed →
added to `missing_prerequisites`.

```json
{
  "need_id": "gd_req__abs_pump_activation",
  "artefact_type": "gd_req",
  "current_state": "draft",
  "target_state": "valid",
  "legal": false,
  "missing_prerequisites": ["independent_review_complete"],
  "transition_path": ["draft", "valid"],
  "notes": [
    "Prerequisite 'independent_review_complete' cannot be confirmed from needs.json fields — manual verification required"
  ]
}
```

```
Resolve missing prerequisites or fix the state declaration before performing the transition.
```

**Variant — current state only (no target_state):**

```json
{
  "need_id": "gd_req__abs_pump_activation",
  "artefact_type": "gd_req",
  "current_state": "draft",
  "target_state": null,
  "legal": true,
  "missing_prerequisites": [],
  "transition_path": null,
  "notes": []
}
```

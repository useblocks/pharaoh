---
name: pharaoh-verify
description: Use when checking whether one sphinx-needs artefact actually addresses the substance of every parent it links to via :satisfies: or :verifies:. Cross-need content check — distinct from structural MECE, schema-level tailor-review, and per-axis req-review/arch-review.
chains_from: [pharaoh-author, pharaoh-req-draft, pharaoh-arch-draft, pharaoh-vplan-draft]
chains_to: [pharaoh-mece]
---

# pharaoh-verify

## When to use

Invoke when the user has one need-id (drafted, modified, or already-published) and wants to
know whether its body actually addresses the substance of its parent — does the architecture
element discharge the requirement, does the test case exercise the requirement's claim, does
the decision close the question its `:decides:` target raised.

This is a **cross-need content check**. It is the only Pharaoh skill that compares two needs'
bodies for substantive coverage.

How it differs from the neighbouring review skills:

| Skill | Scope | Question answered |
|---|---|---|
| `pharaoh-mece` | full corpus | Are required links present? Are there orphans / gaps? (structural) |
| `pharaoh-tailor-review` | tailoring files | Does `.pharaoh/project/` validate against the schemas? (schema-level) |
| `pharaoh-req-review` | one requirement | Does this requirement pass the 11 ISO 26262 §6 axes? (per-axis prose rubric) |
| `pharaoh-arch-review` | one architecture element | Same axes plus arch-specific axes (per-axis prose rubric) |
| `pharaoh-vplan-review` | one test case | Same axes plus vplan-specific axes (per-axis prose rubric) |
| **`pharaoh-verify`** | one child + its parents | Does the child's body actually address the parent's substance? (content-level satisfaction) |

Do NOT use when:

- The user wants per-axis prose grading — use `pharaoh-req-review` / `pharaoh-arch-review` /
  `pharaoh-vplan-review`.
- The user wants gap or orphan analysis across the corpus — use `pharaoh-mece`.
- The user wants to know if the tailoring files are well-formed — use `pharaoh-tailor-review`.

---

## Inputs

- **need_id** (from user): the child need-id to verify. Must exist in `needs.json`.
- **transitive** (from user, optional, default `false`): if `true`, walk every `:satisfies:`
  / `:verifies:` link transitively and verify each ancestor pair (child↔direct-parent,
  direct-parent↔grandparent, …). If `false`, verify only the direct parents.
- **tailoring** (from `.pharaoh/project/`):
  - `artefact-catalog.yaml` — read the link-relationship map: which link types carry the
    "satisfies its parent" semantics for each artefact type. Defaults: `:satisfies:` for
    requirements and architecture; `:verifies:` for test cases; `:decides:` for decisions.
  - `id-conventions.yaml` — only used when reporting parent IDs that fail the regex
- **needs.json**: required for body lookup on both child and every parent

---

## Outputs

A single JSON document. Shape:

```json
{
  "need_id": "<child-id>",
  "child_type": "<type>",
  "parents": [
    {
      "parent_id": "<id>",
      "parent_type": "<type>",
      "link_field": "satisfies|verifies|decides",
      "verdict": "addresses|partial|absent|unresolved",
      "score": 3,
      "reason": "one-sentence justification",
      "missing_aspects": ["..."]
    }
  ],
  "overall": "addresses|partial|absent",
  "action_items": ["..."]
}
```

### Verdict scale

Per parent, score the child body on a 0-3 ordinal:

| Score | Verdict | Definition |
|---|---|---|
| 3 | `addresses` | Child body explicitly covers every claim, condition, or actor named in the parent. No substantive aspect of the parent is missing. |
| 2 | `addresses` | Child covers all major claims; minor wording or a marginal sub-claim is paraphrased rather than restated. |
| 1 | `partial` | Child covers some but not all of the parent's substantive claims. Concrete missing aspects are listed in `missing_aspects`. |
| 0 | `absent` | Child body is generic, off-topic, or names the parent ID without substantively addressing the parent's claim. |
| n/a | `unresolved` | Parent ID does not resolve in `needs.json` — record as `unresolved` and skip scoring this pair. |

### Overall

Computed across all parent pairs (excluding `unresolved`):

- `addresses` — every pair scores ≥ 2
- `partial` — at least one pair scores 1, no pair scores 0
- `absent` — at least one pair scores 0

If every parent is `unresolved`, set `overall` to `"absent"` and add an action item naming the
unresolved parents.

---

## Process

### Step 1: Resolve child

Find `needs.json` (check `docs/_build/needs/needs.json`, then `_build/needs/needs.json`, then
any `needs.json` under a `_build` directory). If not found, FAIL:

```
FAIL: needs.json not found. Build the Sphinx project first
(`sphinx-build docs/ docs/_build/`), then re-run this skill.
```

Look up `need_id`. If not present, FAIL:

```
FAIL: need_id "<id>" not found in needs.json.
Verify the ID or build the project.
```

Extract the child's type, body, and the values of every parent-link field that applies to its
type per `artefact-catalog.yaml` (default mapping: requirements → `:satisfies:`; architecture
→ `:satisfies:`; test cases → `:verifies:`; decisions → `:decides:`).

If the child has no parent-link values at all, emit:

```json
{
  "need_id": "<id>",
  "child_type": "<type>",
  "parents": [],
  "overall": "absent",
  "action_items": [
    "Child has no :satisfies:/:verifies:/:decides: link. Add a parent before verifying."
  ]
}
```

and stop.

---

### Step 2: Resolve parents

For each parent ID listed in the child's link fields, look it up in `needs.json`:

- If found, capture the parent's type and body.
- If not found, mark the pair `verdict: "unresolved"` and continue.

If `transitive = true`, push each resolved parent onto a queue and repeat Step 2 for its own
parents. Maintain a visited set to avoid cycles. The output `parents` list is flattened —
each parent appears once with its direct child noted in `link_field`.

---

### Step 3: Score each pair

For each (child, parent) pair, read both bodies and answer the satisfaction question for the
relevant link semantics:

| Link field | Question to answer |
|---|---|
| `satisfies` | Does the child's prose discharge the parent requirement's claim — i.e. would building only what the child describes satisfy what the parent demands? |
| `verifies` | Does the test case's inputs / steps / expected outcome exercise the specific behaviour the parent requires? Would a passing run of this test give evidence the parent is met? |
| `decides` | Does the decision body resolve the design question that the affected need raises — alternatives weighed, choice stated, rationale matches the parent's concern? |

Score on the 0-3 scale above. Be concrete in `reason` — name the parent claim that is or is
not covered. When `score < 2`, populate `missing_aspects` with the specific claims, actors,
or conditions from the parent that the child fails to address.

For test cases, also flag `partial` when the test only exercises a happy path while the
parent requires negative or boundary cases.

---

### Step 4: Compute overall and action items

Compute `overall` per the table above. For every pair with `score < 2` or
`verdict == "unresolved"`, add a concrete action item naming the parent and the missing
aspect:

```
"satisfies <parent_id>: child does not cover <missing aspect>; rewrite the body to address it"
```

If every pair scores ≥ 2, `action_items` is an empty array.

---

### Step 5: Emit JSON

Emit the JSON document only. No prose wrapper.

If `overall != "addresses"`, append below the JSON a single advisory line:

```
Consider `pharaoh-author <need_id>` to revise the body, or `pharaoh-req-regenerate <need_id>`
for a per-axis driven rewrite. Re-run `pharaoh-verify <need_id>` after the edit.
```

This is the only prose permitted after the JSON.

---

## Guardrails

**G1 — Child not found**

`need_id` absent from `needs.json` → FAIL (Step 1).

**G2 — Child has no parent links**

Emit a JSON document with empty `parents` and a clear action item, then stop (Step 1). Do not
guess a parent.

**G3 — All parents unresolved**

Set `overall = "absent"`; do not crash. Action items must list every unresolved parent ID so
the user can fix the link or build the project first.

**G4 — Empty bodies**

If either the child's body or a parent's body is empty (only the title is set), score that
pair `0` with `reason: "<role> body is empty — substantive verification not possible"` and
add an action item to populate the body before re-running.

---

## Advisory chain

This skill has `chains_to: [pharaoh-mece]` because content satisfaction is the natural sibling
of structural MECE. After verifying one need, the user often wants the corpus-wide structural
view next:

```
Consider running `pharaoh-mece` to confirm the surrounding link structure
(orphans, gaps, status inconsistencies) is also healthy.
```

Show this line only when `overall == "addresses"`.

---

## Worked example

**User input:**

> need_id: `arch__abs_pump_driver`
> transitive: false

**Step 1:** child resolves; type `arch`. Parent-link field for `arch` is `:satisfies:`. Value:
`gd_req__abs_pump_activation`.

**Step 2:** parent resolves. Body: "The brake controller shall engage the ABS pump when
measured wheel slip exceeds the calibrated activation threshold."

**Step 3:** child body: "The ABS pump driver component manages the pump drive circuit,
controlling output PWM duty cycle and providing over-current protection for the pump motor."

The child names the pump drive circuit and the actuation mechanism (PWM, over-current) but
does not state how the wheel-slip-threshold trigger reaches the driver. Score 2 — addresses
the actuation claim but the trigger linkage is implicit.

**Step 4:** `overall = "addresses"`; one minor `missing_aspect` recorded.

**Step 5 output:**

```json
{
  "need_id": "arch__abs_pump_driver",
  "child_type": "arch",
  "parents": [
    {
      "parent_id": "gd_req__abs_pump_activation",
      "parent_type": "gd_req",
      "link_field": "satisfies",
      "verdict": "addresses",
      "score": 2,
      "reason": "child covers pump actuation and protection; the wheel-slip trigger linkage is implicit, not restated",
      "missing_aspects": ["wheel-slip-threshold trigger pathway from sensor to driver"]
    }
  ],
  "overall": "addresses",
  "action_items": []
}
```

```
Consider running `pharaoh-mece` to confirm the surrounding link structure is also healthy.
```

---

**Variant: child does not address the parent**

Same parent, but the child body reads: "The ABS pump driver component logs telemetry every
100 ms to the CAN bus." Logging is unrelated to the parent's actuation claim.

```json
{
  "need_id": "arch__abs_pump_driver",
  "child_type": "arch",
  "parents": [
    {
      "parent_id": "gd_req__abs_pump_activation",
      "parent_type": "gd_req",
      "link_field": "satisfies",
      "verdict": "absent",
      "score": 0,
      "reason": "child describes telemetry logging only; does not address pump engagement on slip threshold",
      "missing_aspects": [
        "ABS pump engagement actuation",
        "wheel-slip-threshold trigger pathway"
      ]
    }
  ],
  "overall": "absent",
  "action_items": [
    "satisfies gd_req__abs_pump_activation: child does not cover pump engagement; rewrite the body to describe the actuation pathway and the slip-threshold trigger"
  ]
}
```

```
Consider `pharaoh-author arch__abs_pump_driver` to revise the body, or `pharaoh-req-regenerate
arch__abs_pump_driver` for a per-axis driven rewrite. Re-run `pharaoh-verify
arch__abs_pump_driver` after the edit.
```

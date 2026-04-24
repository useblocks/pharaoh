---
name: pharaoh-decision-review
description: Use when auditing a single recorded decision (DR / ADR / design note) against the generic decision review axes in `shared/checklists/decision.md`. Checks context/alternatives/consequences structure, traceability to affected artefacts, rationale completeness. Emits structured findings JSON.
chains_from: [pharaoh-decision-record]
chains_to: []
---

# pharaoh-decision-review

## When to use

Invoke after `pharaoh-decision-record` wrote a decision memory. Part of the self-review invariant.

## Atomicity

- (a) One decision + one checklist in → one findings JSON out.
- (b) Input: `{target: <decision_rst_or_memory_id>, checklist_path: <path>, tailoring_path: <path>}`. Output: findings JSON.
- (c) Reward: fixtures `passing-decision.rst` + `failing-decision.rst` with expected findings.
- (d) Reusable.
- (e) Read-only.

## Input

- `target`: RST directive block for a `decision` directive, OR a Papyrus memory_id of type `decision`.
- `checklist_path`: `shared/checklists/decision.md`.

## Output

```json
{
  "need_id": "dr__example",
  "type": "decision",
  "axes": {
    "context_section_present":    {"passed": true},
    "alternatives_listed":        {"passed": true, "reason": "3 alternatives + chosen=4"},
    "consequences_section_present":{"passed": true},
    "trace_to_affected_artefacts":{"passed": true, "reason": "links 2 reqs and 1 arch"},
    "canonical_name_unique":      {"passed": true, "reason": "no dup in papyrus"},
    "rationale_quality":          {"score": 3}
  },
  "overall": "pass"
}
```

## Review axes

See [`shared/checklists/decision.md`](../shared/checklists/decision.md).

---
name: pharaoh-fmea-review
description: Use when auditing a single FMEA entry (failure-mode row) against the generic FMEA review axes in `shared/checklists/fmea.md` plus per-project addenda. Checks severity/occurrence/detection scales, RPN computation, cause/effect well-formedness, traceability to the analyzed artefact. Emits structured findings JSON.
chains_from: [pharaoh-fmea]
chains_to: []
---

# pharaoh-fmea-review

## When to use

Invoke after `pharaoh-fmea` emitted a single failure-mode entry. Part of the self-review invariant.

Do NOT review sets of FMEA rows — this skill reviews one entry. A fleet review is a separate flow that invokes this skill per entry.

## Atomicity

- (a) One FMEA entry + one checklist in → one findings JSON out.
- (b) Input: `{target: <fmea_entry_json_or_need_id>, checklist_path: <path>, tailoring_path: <path>}`. Output: findings JSON.
- (c) Reward: fixtures `passing-fmea.json` + `failing-fmea.json` with expected findings.
- (d) Reusable.
- (e) Read-only.

## Input

- `target`: JSON object with the FMEA entry shape emitted by `pharaoh-fmea`, OR a need_id with type `fmea` in needs.json.
- `checklist_path`: `shared/checklists/fmea.md`.
- `tailoring_path`: `.pharaoh/project/` for optional scale extensions.

## Output

```json
{
  "need_id": "fmea__example_01",
  "type": "fmea",
  "axes": {
    "trace_to_analyzed_artefact":   {"passed": true},
    "severity_in_range":            {"passed": true, "reason": "sev=7, scale=1..10"},
    "occurrence_in_range":          {"passed": true, "reason": "occ=4"},
    "detection_in_range":           {"passed": true, "reason": "det=3"},
    "rpn_computed_correctly":       {"passed": true, "reason": "7*4*3=84, entry reports 84"},
    "cause_well_formed":            {"score": 3},
    "effect_well_formed":           {"score": 3},
    "mitigation_proposed_if_rpn_high": {"score": 2, "reason": "RPN 84 > threshold 60; mitigation text thin"}
  },
  "overall": "pass"
}
```

## Review axes

See [`shared/checklists/fmea.md`](../shared/checklists/fmea.md).

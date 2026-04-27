---
name: pharaoh-diagram-review
description: Use when auditing a single diagram block (Mermaid or PlantUML) emitted by any diagram-emitting skill. Single review atom covering all diagram types — trace/caption/element-count/parser/required-elements checks plus LLM-judge axes for purpose clarity and granularity consistency. Per-type required-element checks dispatched based on `diagram_type` input.
chains_from: [pharaoh-feat-component-extract, pharaoh-feat-flow-extract, pharaoh-use-case-diagram-draft, pharaoh-sequence-diagram-draft, pharaoh-component-diagram-draft, pharaoh-class-diagram-draft, pharaoh-state-diagram-draft, pharaoh-activity-diagram-draft, pharaoh-block-diagram-draft, pharaoh-deployment-diagram-draft, pharaoh-fault-tree-diagram-draft]
chains_to: []
---

# pharaoh-diagram-review

## When to use

Invoke after any diagram-emitting skill produced a single diagram block. Part of the self-review invariant — every `*-diagram-draft` and `*-extract` skill chains into this review.

One diagram per invocation. A plan emitting N diagrams invokes this skill N times.

## Atomicity

- (a) One diagram block + one checklist + one diagram_type in → one findings JSON out. No multi-diagram aggregation, no re-emission.
- (b) Input: `{diagram_block: <rst_directive_string>, diagram_type: <one of 11 canonical types>, parent_need_id: <str>, checklist_path: <path>, tailoring_path: <path>}`. Output: findings JSON with per-axis entries, mirroring `pharaoh-req-review` shape.
- (c) Reward: fixtures for each diagram_type — `passing-<type>.rst` + `failing-<type>.rst` with expected findings. Mechanized axes verified by grep / mmdc / plantuml; subjective axes spot-checked against golden JSON.
- (d) Reusable for every diagram-emitting skill regardless of renderer (mermaid / plantuml).
- (e) Read-only. Does not re-emit or modify the diagram.

## Input

- `diagram_block`: the full RST directive (`.. mermaid::` or `.. uml::`) including options and body, as a single string. Must be the complete directive, not just the body.
- `diagram_type`: one of `use_case | sequence | component | class | state | activity | block | deployment | fault_tree | feat_component_extract | feat_flow_extract`. Determines which per-type required-elements check runs.
- `parent_need_id`: need_id of the artefact the diagram is attached to (feat, arch, comp_req). Used for `trace_to_parent` check.
- `checklist_path`: `shared/checklists/diagram.md`. Per-project additions loaded from `.pharaoh/project/checklists/diagram.md` if present.
- `tailoring_path`: `.pharaoh/project/` for renderer preference and element-count threshold.

## Output

```json
{
  "parent_need_id": "FEAT_jama_import",
  "diagram_type": "sequence",
  "renderer": "mermaid",
  "axes": {
    "trace_to_parent":               {"passed": true, "reason": "caption names FEAT_jama_import"},
    "caption_present":                {"passed": true},
    "element_count_within_bounds":   {"passed": true, "reason": "7 participants, limit 12"},
    "parser_clean":                  {"passed": true, "reason": "mmdc exit 0"},
    "required_elements_for_type":    {"passed": true, "reason": "≥2 participants, ≥1 message"},
    "conditional_branches_marked":   {"passed": true, "reason": "source has 2 branches; diagram uses 1 alt block"},
    "external_library_participant":  {"passed": true, "reason": "requests imported and called; participant Requests present"},
    "returns_match_call_stack":      {"passed": true, "reason": "4 returns, all terminate at prior caller or entrypoint"},
    "purpose_clarity":               {"score": 3},
    "granularity_consistency":       {"score": 3},
    "naming_clarity":                {"score": 3}
  },
  "overall": "pass"
}
```

Axes `conditional_branches_marked`, `external_library_participant`, and `returns_match_call_stack` apply only to the diagram types noted in [`shared/checklists/diagram.md`](../shared/checklists/diagram.md). When a diagram's `diagram_type` falls outside the applicable set (e.g. `class`, `state`, `deployment`), the corresponding axis entry is `{"passed": "n/a", "reason": "axis applies only to sequence diagrams"}` and does NOT contribute to `overall`.

## Review axes

See [`shared/checklists/diagram.md`](../shared/checklists/diagram.md) for the canonical axes. Per-type required-elements:

| diagram_type      | Required elements                                                    |
| ----------------- | -------------------------------------------------------------------- |
| use_case          | ≥1 actor, 1 system boundary (`rectangle`/`package`), ≥1 use case     |
| sequence          | ≥2 participants, ≥1 message                                          |
| component         | ≥1 component node, ≥1 interface or arrow                             |
| class             | ≥1 class node with at least one field OR one method                  |
| state             | 1 initial pseudo-state, 1 final pseudo-state, ≥1 transition          |
| activity          | 1 start node, 1 end node, ≥1 action                                  |
| block (BDD / IBD) | BDD: ≥1 block with `<<block>>` stereotype. IBD: ≥1 port, ≥1 connector |
| deployment        | ≥1 node (physical), ≥1 artefact deployed                             |
| fault_tree        | 1 top event, ≥1 gate (AND/OR), ≥1 basic event                        |
| feat_component_extract | ≥1 file node, ≥1 import arrow                                   |
| feat_flow_extract | ≥1 participant, ≥1 call arrow                                        |

## Composition

Invoked explicitly as a task in plans emitted by `pharaoh-write-plan`, directly after every diagram-emitting task. Coverage enforced by `pharaoh-self-review-coverage-check`.

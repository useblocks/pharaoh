---
name: pharaoh-activity-diagram-draft
description: Use when drafting one activity diagram showing control flow (actions, decisions, forks/joins, swimlanes) for one procedure or algorithm. Typical ASPICE usage — SWE.3 Software Detailed Design. Renderer tailored via `pharaoh.toml`. Does NOT emit other diagram kinds. Status — PLANNED (design-only scaffold; invoking returns sentinel FAIL until implemented).
---

# pharaoh-activity-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-activity-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.activity]`.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one activity diagram. Captures **control flow** within a single procedure: sequential actions, branching (decisions), forking (parallel activities), joining, and swimlanes (partitions) showing which actor/component performs which action.

Typical ASPICE context:
- **SWE.3 Software Detailed Design**: algorithm breakdown per function.
- **SYS.3 System Architectural Design**: activity within a subsystem.

Does NOT capture ordered inter-component message exchange (→ `pharaoh-sequence-diagram-draft`). Does NOT capture state lifecycle (→ `pharaoh-state-diagram-draft`).

## Atomicity

- (a) One procedure in → one diagram out.
- (b) Input: `{view_title: str, actions: list[ActionSpec], decisions: list[DecisionSpec], forks: list[ForkSpec], edges: list[EdgeSpec], initial: str, finals: list[str], swimlanes?: list[SwimlaneSpec], project_root: str, renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `ActionSpec = {id: str, label: str, swimlane?: str}`, `DecisionSpec = {id: str, label: str, swimlane?: str}`, `ForkSpec = {id: str, kind: "fork"|"join", swimlane?: str}`, `EdgeSpec = {from: str, to: str, guard?: str, label?: str}`, `SwimlaneSpec = {id: str, label: str}`. Output: one RST directive block.
- (c) Reward: fixture — procedure `receive_can_frame` with actions [parse, validate, dispatch], one decision (valid?), two finals (accepted, rejected). Scorer:
  1. Output starts with renderer directive.
  2. Exactly one initial marker (`[*]` or equivalent) pointing to `initial`.
  3. Every action/decision/fork id appears as a node.
  4. Every edge renders with renderer-specific syntax; guards shown in `[...]`.
  5. Swimlanes (if any) group their members visually (Mermaid: no native swimlane, emit comment + `subgraph`; PlantUML: `|SwimlaneX|` partition).
  6. Every id in `finals` has an outgoing edge to `[*]`.
  
  Pass = all 6.
- (d) Reusable for any procedural spec: SW detailed design, system workflows, operator procedures.
- (e) One diagram per call.

## Dangling edges

FAIL on edge endpoint not in `actions ∪ decisions ∪ forks ∪ {initial}`. An activity diagram with a transition to an undeclared action is an incomplete procedure.

## Output

**PlantUML (preferred for swimlane support):**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   |Driver|
   start
   :parse CAN frame;
   if (valid?) then (yes)
     |Dispatcher|
     :dispatch to handler;
     stop
   else (no)
     |Driver|
     :log error;
     end
   endif
   @enduml
```

**Mermaid (limited — no native swimlanes):**
```rst
.. mermaid::
   :caption: <view_title>

   flowchart TD
       Start([Start]) --> Parse[parse CAN frame]
       Parse --> Valid{valid?}
       Valid -->|yes| Dispatch[dispatch to handler]
       Valid -->|no| Log[log error]
       Dispatch --> End([End])
       Log --> End
```

## Non-goals

- No pin/action-parameter visualization — out of scope.
- No code-to-activity extraction — caller provides the structure; a future `pharaoh-activity-from-cfg` could infer from control-flow graphs.
- No interrupt/exception flows — model those as explicit edges if needed.

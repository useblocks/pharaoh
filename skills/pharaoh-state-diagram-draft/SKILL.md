---
name: pharaoh-state-diagram-draft
description: Use when drafting one state-machine diagram showing lifecycle or behavioral states of a component/entity, with labeled transitions. Renderer tailored via `pharaoh.toml`. Does NOT emit component, sequence, or class diagrams. Status — PLANNED (design-only scaffold; invoking returns sentinel FAIL until implemented).
---

# pharaoh-state-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-state-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.state]`.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / transition label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one state-machine diagram. Captures **discrete states** of a component/entity and **labeled transitions** between them, with optional events, guards, and actions per transition.

Does NOT capture static structure (→ `pharaoh-component-diagram-draft`, `pharaoh-class-diagram-draft`). Does NOT capture ordered multi-participant interactions (→ `pharaoh-sequence-diagram-draft`).

## Atomicity

- (a) One state machine in → one diagram out. Nested state machines (composite states) are one machine; two independent machines = two skill invocations.
- (b) Input: `{view_title: str, states: list[StateSpec], transitions: list[TransitionSpec], initial_state: str, terminal_states?: list[str], project_root: str, renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `StateSpec = {id: str, label: str, kind?: "simple"|"composite"|"choice"|"junction", sub_states?: list[StateSpec], entry?: str, exit?: str}`, `TransitionSpec = {from: str, to: str, event?: str, guard?: str, action?: str}`. Output: one RST directive block.
- (c) Reward: fixture — lifecycle `draft → in_review → approved → published`, plus `rejected` terminal off `in_review`. Scorer:
  1. Output starts with renderer-specific directive.
  2. Exactly one initial-state marker (`[*] -->` Mermaid, `[*] -->` PlantUML).
  3. `initial_state` is the target of the initial-state arrow.
  4. Every ID in `states` appears as a state node.
  5. Every transition renders with correct arrow and label (`event [guard] / action`).
  6. Every ID in `terminal_states` has a transition `→ [*]`.
  7. With a composite state containing sub_states, the sub-states are nested inside the composite (Mermaid: `state Foo { ... }`; PlantUML: `state Foo { ... }`).
  
  Pass = all 7.
- (d) Reusable: any lifecycle (workflow states, device modes, protocol states, order status machine).
- (e) One machine per call.

## Input highlights

- `states`: all states, possibly nested via `sub_states`. Composite states declare `kind = "composite"`.
- `transitions`: `from`/`to` reference state IDs, including sub-state IDs (cross-boundary transitions supported).
- `initial_state`: REQUIRED. Must be an ID in `states`. There is exactly one initial state; if the machine has multiple "entry points" from outer context, model them via transitions from `[*]` at the composite level.
- `terminal_states` (optional): list of IDs that have implicit transition to `[*]` (final pseudo-state). A machine may have zero terminal states (infinite loop) — valid.

## Transition label format

Renderer-independent format: `event [guard] / action`.
- `event` optional (unlabeled transition = auto).
- `guard` in square brackets, optional.
- `action` after slash, optional.

If all three are absent, render an unlabeled arrow.

## Output

**Mermaid:**
```rst
.. mermaid::
   :caption: <view_title>

   stateDiagram-v2
       [*] --> draft
       draft --> in_review : submit
       in_review --> approved : approve [reviewer_count >= 2]
       in_review --> rejected : reject / notify_author
       approved --> published : publish
       rejected --> [*]
       published --> [*]
```

**PlantUML:**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   [*] --> draft
   draft --> in_review : submit
   in_review --> approved : approve [reviewer_count >= 2]
   in_review --> rejected : reject / notify_author
   approved --> published : publish
   rejected --> [*]
   published --> [*]
   @enduml
```

## Non-goals

- No state-from-code extraction — callers supply states and transitions explicitly. A future `pharaoh-states-from-source` skill could infer from match statements / switch / FSM libraries, but is a separate concern.
- No timing annotations (real-time deadlines, timer events) — sequence diagrams are a better fit for temporal constraints.
- No concurrency regions by default — a future extension may add orthogonal regions; for now, sub_states are strictly hierarchical.
- No auto-detection of terminal states — caller provides them.

## Interaction with tailoring

Some projects (e.g. workflow-heavy ubproject.toml with lifecycle state enums) already declare state machines implicitly — sphinx-needs `status` enum is a two-line state machine. A caller might want to derive the diagram from the project's `workflows.yaml` (when present). That derivation is NOT this skill's concern; the caller invokes `pharaoh-state-diagram-draft` with explicit `states` and `transitions`. A wrapper that reads `workflows.yaml` and calls this skill is orchestration, not atomic.

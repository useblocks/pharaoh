---
name: pharaoh-fault-tree-diagram-draft
description: Use when drafting one fault tree for FTA (Fault Tree Analysis) — a top hazard event decomposed through AND/OR gates into basic events (component failures, random hardware faults, human errors). Typical ISO 26262 usage — Part 3 Hazard Analysis & Risk Assessment, and Part 5 supporting hardware architectural metrics. Renderer tailored via `pharaoh.toml`. Status — PLANNED (design-only scaffold; invoking returns sentinel FAIL until implemented).
---

# pharaoh-fault-tree-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-fault-tree-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.fault_tree]`.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one fault tree. Captures top-down deductive decomposition of one **top hazard event** via logical gates (AND, OR, NOT, inhibit, priority-AND, exclusive-OR) into **intermediate events** and **basic events** with optional failure probabilities.

Typical ISO 26262 context:
- **Part 3 HARA**: qualitative fault trees identifying top-level hazards.
- **Part 5 §9 Hardware architectural metrics (SPFM, LFM, PMHF)**: quantitative fault trees — each basic event has a failure rate λ; the tree propagates to the top event.
- **Safety case argumentation**: showing how a safety goal violation would have to occur, and what barriers prevent it.

## Atomicity

- (a) One top event in → one tree out.
- (b) Input: `{view_title: str, top_event: EventSpec, gates: list[GateSpec], basic_events: list[BasicEventSpec], edges: list[TreeEdgeSpec], project_root: str, show_probabilities?: bool, renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `EventSpec = {id: str, label: str, probability?: float}`, `GateSpec = {id: str, kind: "AND"|"OR"|"NOT"|"INHIBIT"|"PAND"|"XOR", label?: str}`, `BasicEventSpec = {id: str, label: str, probability?: float, kind?: "hardware"|"software"|"human"|"environmental"}`, `TreeEdgeSpec = {from: str, to: str}` (tree edges go from parent to child, parent = top event or gate, child = gate or basic event). Output: one RST directive block.
- (c) Reward: fixture — top event "Unintended Acceleration", OR gate decomposing to [ECU software fault, sensor stuck signal], sensor fault AND-gated by [sensor failure, fallback disabled]. Scorer:
  1. Output starts with renderer directive.
  2. Top event appears at the graph root (no incoming edges).
  3. Every gate rendered with UML / FTA-standard shape: AND = flat-bottom D, OR = curved-bottom D, NOT = triangle with bar, etc. (Mermaid approximation: labeled diamond + annotation.)
  4. Basic events rendered as circles (standard FTA notation) or leaves.
  5. With `show_probabilities=true`, every event/basic-event with a `probability` shows it numerically; gates show computed result if all children have probabilities.
  6. No basic event has outgoing edges (leaves).
  7. Every non-leaf node has ≥1 outgoing edge (gates can't be childless).
  
  Pass = all 7.
- (d) Reusable across safety-critical domains (automotive, medical, aerospace, industrial).
- (e) One tree per call.

## Dangling edges / cycles

- FAIL on edge endpoint not in `{top_event} ∪ gates ∪ basic_events`.
- FAIL on cycle (fault trees are DAGs; a cycle means the model is wrong).
- FAIL if the top event has an incoming edge (root must be the top).

## Output

**PlantUML (has dedicated FTA symbols via GraphViz DOT syntax embedded):**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   skinparam defaultFontSize 11
   rectangle "TOP:\nUnintended Acceleration\nλ=1e-8/h" as TOP
   rectangle "OR" as G1
   rectangle "AND" as G2
   circle "Sensor stuck\nλ=5e-7/h" as BE1
   circle "ECU SW fault\nλ=2e-8/h" as BE2
   circle "Fallback disabled\nλ=1e-6/h" as BE3
   TOP --> G1
   G1 --> BE2
   G1 --> G2
   G2 --> BE1
   G2 --> BE3
   @enduml
```

**Mermaid (flowchart approximation — no native FTA gate shapes):**
```rst
.. mermaid::
   :caption: <view_title>

   flowchart TD
       TOP["TOP: Unintended Acceleration<br/>λ=1e-8/h"]
       G1{{OR}}
       G2{{AND}}
       BE1(("Sensor stuck<br/>λ=5e-7/h"))
       BE2(("ECU SW fault<br/>λ=2e-8/h"))
       BE3(("Fallback disabled<br/>λ=1e-6/h"))
       TOP --> G1
       G1 --> BE2
       G1 --> G2
       G2 --> BE1
       G2 --> BE3
```

## Interaction with `pharaoh-fmea`

FMEA and FTA are complementary: FMEA is bottom-up (component → effect), FTA is top-down (hazard → component). Pharaoh already has `pharaoh-fmea` for FMEA entries. A future orchestrator (`pharaoh-hazard-analysis`) may pair the two: extract top hazards from FMEA entries with high RPN, then generate FTA per hazard. Out of scope here.

## Non-goals

- No cut-set minimization — quantitative FTA tools (e.g. FaultTree+, CAFTA) handle this; this skill just emits the tree structure.
- No probability computation beyond trivial AND-of-independents / OR-of-independents — caller provides computed probabilities if needed.
- No dynamic fault trees (Markov chains, repair rates) — static FT only.
- No common-cause-failure (CCF) modeling — would need extra node kind; a future extension.

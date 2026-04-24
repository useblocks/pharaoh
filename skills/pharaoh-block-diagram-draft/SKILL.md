---
name: pharaoh-block-diagram-draft
description: Use when drafting one SysML-style block diagram — Block Definition Diagram (BDD) showing block structure and composition, or Internal Block Diagram (IBD) showing ports, flows, and part interconnections. Typical ASPICE usage — SYS.2/SYS.3 for system-level architecture, and SWE.2 for software architecture on SysML-heavy projects. Renderer tailored via `pharaoh.toml`.
---

# pharaoh-block-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-block-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.block]`.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one block diagram, either a **BDD** (structural — blocks, parts, value properties, composition hierarchy) or **IBD** (internal — parts, ports, item flows, constraint properties). Which variant is rendered depends on input: presence of `ports` and `flows` implies IBD; absence implies BDD.

Typical ASPICE context:
- **SYS.2 System Requirements Analysis**: BDD for the system under analysis.
- **SYS.3 System Architectural Design**: BDD for subsystem decomposition; IBD for internal wiring.
- **SWE.2 Software Architectural Design**: same, applied at SW component level.

Distinct from `pharaoh-component-diagram-draft` (UML component view — looser, allows external ghost nodes) because BDD/IBD are closed SysML models with strict composition semantics.

## Atomicity

- (a) One block scope in → one diagram out. Variant (BDD vs IBD) inferred from input presence.
- (b) Input: `{view_title: str, blocks: list[BlockSpec], parts: list[PartSpec], compositions: list[CompositionSpec], ports?: list[PortSpec], flows?: list[FlowSpec], associations?: list[AssocSpec], project_root: str, variant_override?: "bdd"|"ibd", renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `BlockSpec = {id: str, label: str, stereotype?: "block"|"subsystem"|"valueType", value_properties?: list[str], operations?: list[str]}`, `PartSpec = {id: str, label: str, type_id: str, multiplicity?: str}`, `CompositionSpec = {whole: str, part: str, label?: str}`, `PortSpec = {id: str, label: str, direction: "in"|"out"|"inout", owner_block_or_part: str}`, `FlowSpec = {from_port: str, to_port: str, item_type?: str, label?: str}`, `AssocSpec = {from: str, to: str, kind: "reference"|"depend", label?: str}`. Output: one RST directive block.
- (c) Reward: two fixtures.

  **BDD fixture** — blocks [Vehicle, ECU, Sensor], composition Vehicle◆━ECU, Vehicle◆━Sensor. Scorer:
  1. Output starts with renderer directive.
  2. Every block rendered with `<<block>>` stereotype.
  3. Compositions rendered with filled-diamond arrow.
  4. Value properties (if any) shown inside block compartments.
  5. `ports`/`flows` absent → no IBD syntax emitted.
  
  Pass = all 5.

  **IBD fixture** — one block Vehicle with parts ecu:ECU, sensor:Sensor, ports [Vehicle.can_out: out, ECU.can_in: in], one flow Vehicle.can_out → ECU.can_in item_type=CANFrame. Scorer:
  1. Output starts with renderer directive.
  2. The enclosing block rendered as the diagram frame.
  3. Parts rendered inside the frame with `:TypeName` notation.
  4. Ports rendered on the boundary (block port) or inside (part port), with direction indicated (triangle/arrow).
  5. Flows rendered with item type label.
  6. All ports / parts have valid `owner_block_or_part` references.
  
  Pass = all 6.

- (d) Reusable for any SysML-based systems engineering workflow.
- (e) One diagram per call.

## Dangling references

FAIL on `part.type_id` not in `blocks`, `composition.whole`/`composition.part` not in `blocks ∪ parts`, `port.owner_block_or_part` not in `blocks ∪ parts`, `flow.from_port`/`flow.to_port` not in `ports`.

## Output

**PlantUML (SysML-style; BDD):**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   class Vehicle <<block>> {
     + mass : kg
   }
   class ECU <<block>>
   class Sensor <<block>>
   Vehicle *-- "1" ECU : ecu
   Vehicle *-- "1..*" Sensor : sensor
   @enduml
```

**PlantUML (IBD):**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   rectangle "Vehicle" as veh {
     component "ecu : ECU" as ecu
     component "sensor : Sensor" as sns
   }
   portout "can_out" as p1
   portin "can_in" as p2
   veh - p1
   ecu - p2
   p1 --> p2 : <<flow>> CANFrame
   @enduml
```

**Mermaid** — no native SysML support; render as annotated flowchart with stereotypes in labels. Emit a `%% NOTE: Mermaid approximation of SysML block diagram` comment.

## Non-goals

- No parametric diagrams (constraint properties with equations) — separate future skill.
- No BDD / IBD round-trip to SysML XMI — out of scope; this skill emits diagrams only.
- No automatic BDD-from-code inference — caller provides structure.

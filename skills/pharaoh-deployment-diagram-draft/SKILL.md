---
name: pharaoh-deployment-diagram-draft
description: Use when drafting one deployment diagram showing physical nodes (ECUs, servers, boards), the software artefacts deployed on each, and communication channels (buses, networks). Typical ASPICE usage — SYS.3 System Architectural Design; essential for automotive HW/SW allocation per ISO 26262 Part 5 (HW) and Part 6 (SW). Renderer tailored via `pharaoh.toml`. Status — PLANNED (design-only scaffold; invoking returns sentinel FAIL until implemented).
---

# pharaoh-deployment-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-deployment-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.deployment]`.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one deployment diagram. Captures **execution environment topology**: physical/virtual nodes, the software artefacts (components, containers, services) deployed on each, and the communication channels between nodes (CAN bus, Ethernet, IPC, HTTP, etc.).

Typical ASPICE / ISO 26262 context:
- **SYS.3 System Architectural Design**: allocation of system elements to HW.
- **ISO 26262 Part 5 (Hardware level)**: mapping safety goals to HW elements.
- **ISO 26262 Part 6 (Software level)**: SW partitioning across ECUs with ASIL tagging.

## Atomicity

- (a) One deployment topology in → one diagram out.
- (b) Input: `{view_title: str, nodes: list[NodeSpec], artefacts: list[ArtefactSpec], deployments: list[DeploymentSpec], channels: list[ChannelSpec], project_root: str, renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `NodeSpec = {id: str, label: str, kind?: "device"|"ecu"|"server"|"cloud"|"container", stereotype?: str, asil?: "A"|"B"|"C"|"D"|"QM"}`, `ArtefactSpec = {id: str, label: str, kind?: "component"|"container"|"library"|"binary"|"config"}`, `DeploymentSpec = {node: str, artefact: str}`, `ChannelSpec = {from: str, to: str, label?: str, protocol?: str}`. Output: one RST directive block.
- (c) Reward: fixture — two ECUs (ECU_A ASIL B, ECU_B ASIL D), three artefacts, deployments mapping artefacts to ECUs, CAN bus channel between them. Scorer:
  1. Output starts with renderer directive.
  2. Every node rendered with cube/node shape.
  3. Every artefact rendered inside its deployed node.
  4. Every channel rendered with labeled arrow and protocol annotation.
  5. ASIL tag (when present) visible on node label or as stereotype.
  6. Deployment without a matching node/artefact → FAIL (dangling deployment).
  
  Pass = all 6.
- (d) Reusable across embedded / distributed / cloud projects; not automotive-specific (ASIL tag is optional).
- (e) One diagram per call.

## Dangling relationships

FAIL on `deployments.node` not in `nodes`, `deployments.artefact` not in `artefacts`, `channels.from`/`channels.to` not in `nodes`.

## Output

**PlantUML (richest deployment syntax):**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   node "ECU_A\n<<ASIL B>>" as ecuA {
     artifact "sensor_driver" as art1
     artifact "can_stack" as art2
   }
   node "ECU_B\n<<ASIL D>>" as ecuB {
     artifact "brake_controller" as art3
   }
   ecuA ..> ecuB : CAN (500kbit/s)
   @enduml
```

**Mermaid:**
```rst
.. mermaid::
   :caption: <view_title>

   flowchart LR
       subgraph ECU_A["ECU_A (ASIL B)"]
         art1[sensor_driver]
         art2[can_stack]
       end
       subgraph ECU_B["ECU_B (ASIL D)"]
         art3[brake_controller]
       end
       ECU_A -.CAN 500kbit/s.-> ECU_B
```

## Non-goals

- No electrical schematic — use dedicated EE tools for that.
- No real-time timing analysis on channels — a separate `pharaoh-timing-diagram-draft` could cover message schedules.
- No auto-derivation from HW description files (e.g. ARXML) — caller provides explicit node and deployment specs.

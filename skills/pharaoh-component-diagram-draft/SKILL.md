---
name: pharaoh-component-diagram-draft
description: Use when drafting one component-relationship diagram (nodes = sphinx-needs, edges = link relations) for a bounded scope — one feature, one module, one architectural view. Renderer tailored via `pharaoh.toml`. Does NOT emit sequence, class, or state diagrams — those are separate skills. Status — PLANNED (design-only scaffold; invoking returns sentinel FAIL until implemented).
---

# pharaoh-component-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-component-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). This skill reads `[pharaoh.diagrams]` and `[pharaoh.diagrams.component]` from the consumer project's `pharaoh.toml`.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one component-relationship diagram (static containment + link-relation edges between needs). Analogue to UML component diagrams, C4 container/component views.

Does NOT show behavior over time (→ `pharaoh-sequence-diagram-draft`). Does NOT show type hierarchies with fields/methods (→ `pharaoh-class-diagram-draft`). Does NOT show lifecycle/FSM (→ `pharaoh-state-diagram-draft`).

## Atomicity

- (a) One scope in → one diagram out. No multi-scope bundling. No mutation of needs.
- (b) Input: `{view_title: str, scope_ids: list[str], project_root: str, renderer_override?: "mermaid"|"plantuml", direction_override?: "TB"|"LR"|"BT"|"RL", ghost_nodes?: bool, on_missing_config?: "fail"|"prompt"|"use_default", papyrus_workspace?: str, reporter_id: str}`. Output: one RST directive block (`.. mermaid::` or `.. uml::`) with caption. No surrounding prose.
- (c) Reward: fixture with 3 in-scope needs (A, B, C) chained A→B→C via `:links:`, plus one out-of-scope need D that B links to. Scorer:
  1. Output starts with the renderer-specific directive matching tailoring.
  2. Every ID in `scope_ids` appears as a node in the diagram body.
  3. Edges A→B and B→C render in renderer syntax (`A --> B`).
  4. With default `ghost_nodes=true`: D appears as a ghost node (dashed outline / muted color / external stereotype), edge B→D is rendered.
  5. With `ghost_nodes=false`: D does NOT appear, edge B→D is dropped, and a warning is logged naming D as a dangling dependency.
  6. `renderer_override="mermaid"` on a PlantUML-tailored project produces Mermaid.
  
  Pass = all 6.
- (d) Reusable for any sphinx-needs project needing static architecture diagrams.
- (e) One phase, one skill. No cross-skill calls.

## Input

- `view_title`: human-readable title (→ diagram caption).
- `scope_ids`: list of sphinx-needs IDs to include. Skill reads each via `ubc` / file fallback to extract type, title, and outgoing link options.
- `project_root`: absolute path to consumer project root. Used for `pharaoh.toml` tailoring lookup.
- `renderer_override` (optional): per-call override. Resolution order in `shared/diagram-tailoring.md`.
- `direction_override` (optional): `TB` | `LR` | `BT` | `RL`. Falls back to `[pharaoh.diagrams.component].direction` → `"TB"`.
- `ghost_nodes` (optional): if `true` (default), edges whose target is outside `scope_ids` render as ghost nodes — dashed outline, muted color, visually distinct from in-scope nodes — so reviewers see the boundary between "our scope" and "external dependencies." If `false`, the dangling edge is dropped and a warning is logged. Default `true`.
- `on_missing_config` (optional): see shared doc. Default `"prompt"`.
- `papyrus_workspace` (optional): for consistent node labeling across diagrams (same canonical names as `pharaoh-req-from-code`).
- `reporter_id`: short agent identifier.

## Output

Single RST directive block. Renderer-dependent body:

**Mermaid (default):**
```rst
.. mermaid::
   :caption: <view_title>

   graph TB
       FEAT_csv_export[CSV Export]:::feat
       CREQ_csv_export_01[Write CSV header row]:::comp_req
       CREQ_csv_export_02[Serialize rows]:::comp_req
       CREQ_csv_export_01 --> FEAT_csv_export
       CREQ_csv_export_02 --> FEAT_csv_export
       classDef feat fill:#4ECDC4
       classDef comp_req fill:#BFD8D2
```

**PlantUML:**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   component "CSV Export" as FEAT_csv_export #4ECDC4
   component "Write CSV header row" as CREQ_csv_export_01 #BFD8D2
   component "Serialize rows" as CREQ_csv_export_02 #BFD8D2
   CREQ_csv_export_01 --> FEAT_csv_export
   CREQ_csv_export_02 --> FEAT_csv_export
   @enduml
```

`classDef`/color fills come from `[pharaoh.diagrams.type_styles]` if tailored; otherwise renderer defaults (no styling).

## Process (sketch)

1. Resolve renderer, direction, type_styles from `pharaoh.toml` (see shared doc for order). If any mandatory field missing AND `on_missing_config == "prompt"` → emit structured proposal.
2. Read each need in `scope_ids` via data-access layer (`ubc` CLI preferred).
3. Build internal graph: nodes = scope_ids, edges = outgoing links.
4. For each edge: if target ∈ scope_ids → render as in-scope edge. If target ∉ scope_ids → behavior depends on `ghost_nodes`:
   - `ghost_nodes=true` (default): add the target as a ghost node (dashed outline, muted color, `<<external>>` stereotype or renderer-equivalent). Render the edge normally. Log info-level note listing all ghost nodes.
   - `ghost_nodes=false`: drop the edge. Log warning naming the dangling pair.
5. Emit renderer-specific syntax. Ghost nodes are grouped visually apart from in-scope nodes where the renderer supports it (Mermaid: separate `subgraph External`; PlantUML: `package "external" { ... }`).
6. Wrap in RST directive with caption.
7. Return.

## Non-goals

- Not sequences, not classes, not state machines — separate skills.
- Not auto-layout tuning — emit simple directional graphs.
- Not diagram-to-needs sync — edges are DERIVED from needs, never a source of truth.

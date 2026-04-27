---
name: pharaoh-sequence-diagram-draft
description: Use when drafting one sequence diagram showing ordered interactions between participants (components, actors, external systems) over time. Renderer tailored via `pharaoh.toml`. Does NOT emit component, class, or state diagrams. Status — PLANNED (design-only scaffold; invoking returns sentinel FAIL until implemented).
---

# pharaoh-sequence-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-sequence-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.sequence]` for per-type overrides.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label / message text MUST be sanitised per that rule set before the block leaves this skill. **Extra sharp for sequence diagrams:** Mermaid 11 treats `;` inside a message label as a statement terminator — prior dogfooding shipped a `J->>J: filter by type; skip SET/Folder` that parsed cleanly under `sphinx-build -nW` but rendered as `Syntax error` in the browser. Always replace `;` with `,` in message labels.

## Purpose

One invocation → one sequence diagram. Captures **ordered interactions over time** between a bounded set of participants. Typical inputs: a feature's "happy path" flow, an interface's request/response trace, an incident timeline reconstructed from logs.

Does NOT capture static containment (→ `pharaoh-component-diagram-draft`). Does NOT capture type relationships (→ `pharaoh-class-diagram-draft`). Does NOT capture state transitions (→ `pharaoh-state-diagram-draft`).

## Atomicity

- (a) One interaction in → one diagram out. No multi-scenario bundling (alt paths in one diagram are OK — they are part of one scenario; but two independent scenarios are two skill invocations).
- (b) Input: `{view_title: str, participants: list[ParticipantSpec], messages: list[MessageSpec], project_root: str, renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `ParticipantSpec = {id: str, label: str, kind?: "actor"|"component"|"boundary"|"database"|"external"}` and `MessageSpec = {from: str, to: str, label: str, kind?: "sync"|"async"|"return"|"self", fragment?: FragmentSpec}`. Output: one RST directive block.
- (c) Reward: fixture with 3 participants (User, API, DB) and 4 messages (User→API: request, API→DB: query, DB→API: result, API→User: response). Scorer:
  1. Output starts with renderer-specific directive.
  2. Every participant id in `participants` is declared in the diagram body.
  3. Every message appears in order (renderer syntax: `User->>API: request` for Mermaid).
  4. Message count in output = `len(messages)`.
  5. Sync vs async arrow differs syntactically (`->>` vs `-)` in Mermaid; `->` vs `->>` in PlantUML).
  6. Self-message (kind=`self`) renders as a self-loop on the participant.
  
  Pass = all 6.
- (d) Reusable: any interaction diagram. Especially valuable for interface/API specs.
- (e) One diagram kind per skill.

## Input

- `view_title`: diagram caption.
- `participants`: ordered list; order = left-to-right placement in the diagram.
- `messages`: ordered list; order = top-to-bottom time axis. Each message references participants by id.
- `project_root`: for tailoring lookup.
- `renderer_override`, `on_missing_config`, `papyrus_workspace`, `reporter_id`: as in shared doc.

### FragmentSpec (optional per message)

```json
{"type": "alt"|"opt"|"loop"|"par"|"critical"|"break", "condition": "<string>"}
```

Groups consecutive messages under a fragment (e.g. `alt`: alternative paths; `loop`: repeated block). If `messages[i].fragment` is non-null, it opens a fragment that stays open until a later message with `fragment = null` or a different fragment type.

This is the one piece of sequence-diagram structure that has no analogue in component diagrams — hence sequence gets its own skill.

## Output

**Mermaid:**
```rst
.. mermaid::
   :caption: <view_title>

   sequenceDiagram
       participant User
       participant API
       participant DB
       User->>API: request
       API->>DB: query
       DB-->>API: result
       API-->>User: response
```

**PlantUML:**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   actor User
   participant API
   database DB
   User -> API : request
   API -> DB : query
   DB --> API : result
   API --> User : response
   @enduml
```

## Process (sketch)

1. Resolve tailoring per shared doc.
2. Emit participant declarations in order (Mermaid: `participant X`; PlantUML: `actor X`/`participant X`/`database X` keyed on `ParticipantSpec.kind`).
3. Emit messages in order. Map `kind` → renderer syntax (sync/async/return/self).
4. Handle fragments: open `alt`/`opt`/`loop` as messages are emitted; close at end of fragment.
5. Wrap in RST directive.

## Non-goals

- No auto-extraction of sequences from code/logs — the caller provides `participants` and `messages` explicitly. A separate future skill (`pharaoh-sequence-from-trace`) could infer these from runtime logs, but that is a different concern.
- No return-arrow inference — if the caller wants a return, they include it as a message with `kind="return"`.
- No activation-bar auto-insertion (PlantUML activates/deactivates) — caller can add via `fragment` or future extension.

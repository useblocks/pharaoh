---
name: pharaoh-class-diagram-draft
description: Use when drafting one class diagram showing a bounded set of types/entities with their fields, methods, and relationships (inheritance, composition, aggregation, association). Renderer tailored via `pharaoh.toml`. Does NOT emit component, sequence, or state diagrams.
---

# pharaoh-class-diagram-draft (PLANNED)

> **Status:** DESIGN ONLY. Implementation sentinel FAIL: `"pharaoh-class-diagram-draft is planned but not implemented; see SKILL.md"`.

Shared tailoring rules: see [`shared/diagram-tailoring.md`](../shared/diagram-tailoring.md). Reads `[pharaoh.diagrams.class]` for per-type overrides.

Safe-label rules: see [`shared/diagram-safe-labels.md`](../shared/diagram-safe-labels.md). Every emitted label / node id / edge label MUST be sanitised per that rule set before the block leaves this skill. `sphinx-build` does not validate diagram bodies — a parse failure becomes visible only at browser render time. Sanitisation is the first line of defence; the second is `pharaoh-diagram-lint` run as part of `pharaoh-quality-gate`.

## Purpose

One invocation → one class/type diagram. Captures **structural relationships** between types: inheritance hierarchies, composition, aggregation, plain association, with optional per-class fields and methods.

Does NOT capture runtime behavior over time (→ `pharaoh-sequence-diagram-draft`). Does NOT capture high-level component topology (→ `pharaoh-component-diagram-draft`). Does NOT capture lifecycle FSM (→ `pharaoh-state-diagram-draft`).

## Atomicity

- (a) One class set in → one diagram out. No splitting across diagrams; if the set is too large to fit, caller invokes multiple times with different scopes.
- (b) Input: `{view_title: str, classes: list[ClassSpec], relationships: list[RelationSpec], project_root: str, show_fields?: bool, show_methods?: bool, visibility_filter?: list["public"|"protected"|"private"], renderer_override?, on_missing_config?, papyrus_workspace?, reporter_id: str}` where `ClassSpec = {id: str, label: str, stereotype?: "abstract"|"interface"|"enum"|"struct", fields?: list[FieldSpec], methods?: list[MethodSpec]}`, `FieldSpec = {name: str, type?: str, visibility?: "public"|"protected"|"private"}`, `MethodSpec = {name: str, params?: str, return_type?: str, visibility?: "public"|"protected"|"private"}`, `RelationSpec = {from: str, to: str, kind: "inherits"|"implements"|"composes"|"aggregates"|"associates"|"depends", label?: str, cardinality_from?: str, cardinality_to?: str}`. Output: one RST directive block.
- (c) Reward: fixture — abstract base `Shape` with method `area()`, concrete `Circle` and `Square` inheriting, plus `Canvas` composing 1..* Shapes. Scorer:
  1. Output starts with renderer-specific directive.
  2. All class IDs declared.
  3. Inheritance edges Circle→Shape, Square→Shape render in inheritance syntax (hollow triangle in both Mermaid/PlantUML).
  4. Composition edge Canvas→Shape renders in composition syntax (filled diamond).
  5. Cardinality `1..*` on composition edge is present.
  6. With `show_fields=false, show_methods=false`, no field/method lines appear.
  7. With `show_methods=true`, abstract `area()` on Shape is rendered with stereotype (italic/abstract marker).
  
  Pass = all 7.
- (d) Reusable: any OOP codebase, domain model extraction, data schema visualization.
- (e) One diagram per call.

## Input highlights (others per shared doc)

- `classes`: declared order = render order (usually doesn't matter for class diagrams but preserved for determinism).
- `relationships`: every `from`/`to` MUST reference a class ID in `classes`. Dangling relationship → FAIL (class diagrams don't tolerate ghost classes in the same way component diagrams tolerate out-of-scope links; either the class is in the diagram or it is not).
- `show_fields` / `show_methods` (optional): default `true`. Set to `false` for overview diagrams.
- `visibility_filter` (optional): include only members matching these visibilities. Default: all.

## Output

**Mermaid:**
```rst
.. mermaid::
   :caption: <view_title>

   classDiagram
       class Shape {
           <<abstract>>
           +area() double
       }
       class Circle {
           -radius: double
           +area() double
       }
       class Canvas {
           +shapes: List~Shape~
       }
       Shape <|-- Circle
       Shape <|-- Square
       Canvas "1" *-- "1..*" Shape
```

**PlantUML:**
```rst
.. uml::
   :caption: <view_title>

   @startuml
   abstract class Shape {
     +area() : double
   }
   class Circle {
     -radius : double
     +area() : double
   }
   class Canvas
   Shape <|-- Circle
   Shape <|-- Square
   Canvas "1" *-- "1..*" Shape
   @enduml
```

## Relationship kind → renderer syntax

| Kind | Mermaid | PlantUML |
|---|---|---|
| `inherits` | `A <|-- B` | `A <|-- B` |
| `implements` | `A <|.. B` | `A <|.. B` |
| `composes` | `A *-- B` | `A *-- B` |
| `aggregates` | `A o-- B` | `A o-- B` |
| `associates` | `A -- B` | `A -- B` |
| `depends` | `A ..> B` | `A ..> B` |

Both renderers converge on UML-standard arrows; the syntax is virtually identical.

## Non-goals

- No generics/template detection — callers pass rendered forms (`List~Shape~`, `Option<T>`) in field types as strings.
- No automatic abstract detection — caller sets `stereotype` explicitly.
- No private-member hiding by default — caller uses `visibility_filter=["public"]` if needed.
- No class-from-code extraction — separate future skill (`pharaoh-classes-from-source`) could infer; out of scope here.

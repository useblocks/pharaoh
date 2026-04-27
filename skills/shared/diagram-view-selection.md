# Diagram view → diagram type selection

Shared reference mapping architectural views to diagram types, consumed by `pharaoh-write-plan` when emitting diagram tasks in a plan DAG.

Defaults below are generic. Projects override via `.pharaoh/project/diagram-conventions.yaml`. Any project not overriding picks up the defaults.

## Default view → diagram-type map

| View (architectural intent)                    | Default diagram skill                        | Notes                                                         |
| ---------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------- |
| Use case (feat level, user-facing)             | `pharaoh-use-case-diagram-draft`             | Actors + system boundary + use cases                          |
| Feature static (feat level, building blocks)   | `pharaoh-component-diagram-draft`            | Logical components and interfaces                             |
| Feature dynamic (feat level, interaction)      | `pharaoh-sequence-diagram-draft` (+ `pharaoh-activity-diagram-draft` for error flows) | Scenario coverage knob in sequence-draft |
| Feature interface                              | `pharaoh-component-diagram-draft`            | With logical interface stereotypes                            |
| Component static (comp level, white-box)       | `pharaoh-class-diagram-draft` OR `pharaoh-component-diagram-draft` | Class for OO languages; component for services |
| Component dynamic                              | `pharaoh-sequence-diagram-draft`             | Internal interactions                                         |
| State behaviour                                | `pharaoh-state-diagram-draft`                | Per stateful component                                        |
| Deployment                                     | `pharaoh-deployment-diagram-draft`           | Physical nodes + artefacts                                    |
| Fault analysis (FTA)                           | `pharaoh-fault-tree-diagram-draft`           | Top event + gates                                             |
| Reverse-engineered static                      | `pharaoh-feat-component-extract`             | Automatic — import graph                                      |
| Reverse-engineered dynamic (call graph)        | `pharaoh-feat-flow-extract`                  | Automatic — call graph                                        |

## Scenario coverage

Dynamic views (`feat_arc_dyn`, `comp_arc_dyn`) may require multiple diagrams covering different scenarios. Projects declare the scenarios in `.pharaoh/project/diagram-conventions.yaml` under `dynamic_view_scenarios`. Defaults:

```yaml
dynamic_view_scenarios:
  - default
```

Single diagram per dynamic view. Projects requiring fuller coverage override, e.g.:

```yaml
dynamic_view_scenarios:
  - success_path
  - error_handling
  - operation_lifecycle  # start-up, shut-down
  - critical_interface
```

`pharaoh-sequence-diagram-draft` and `pharaoh-feat-flow-extract` accept a `scenarios: [...]` input. `pharaoh-write-plan` foreach-expands per scenario when emitting dynamic-view tasks.

## Renderer selection

Default renderer is `mermaid`. Projects override via `.pharaoh/project/diagram-conventions.yaml > renderer`:

```yaml
renderer: plantuml   # or: mermaid
```

All `*-diagram-draft` skills accept `renderer` as input. If unspecified, they read it from the tailoring file.

## Stereotype aliases

Projects using SysML-style stereotypes override the defaults. Example:

```yaml
stereotype_aliases:
  block: "<<block>>"
  component: "<<component>>"
  interface: "<<interface>>"
```

Draft skills consult the alias map when emitting. Defaults: plain UML stereotypes as listed.

## Safety and security markers

Not in the base. Projects with safety/security concerns add axes via tailoring (Score's ASIL markers are an example — see `.pharaoh/project/diagram-conventions.yaml` + `.pharaoh/project/checklists/diagram.md`).

## How plans use this

`pharaoh-write-plan` reads `.pharaoh/project/diagram-conventions.yaml` at plan-write time. For every artefact in the plan that requires a diagram view, it:
1. Looks up `diagram_type` from this mapping (or from project override).
2. Inserts a task invoking the mapped `*-diagram-draft` skill.
3. For dynamic views, foreach-expands over `dynamic_view_scenarios`.
4. Inserts a `pharaoh-diagram-review` task depending on each diagram-draft task.

Review always follows draft — see `shared/self-review-invariant.md`.

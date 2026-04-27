# Diagram tailoring — shared contract for all `pharaoh-*-diagram-draft` skills

Every atomic diagram skill (`pharaoh-component-diagram-draft`, `pharaoh-sequence-diagram-draft`, `pharaoh-class-diagram-draft`, `pharaoh-state-diagram-draft`, future additions) reads renderer and styling config from the consumer project's `pharaoh.toml`. This document is the single source of truth for how that config is shaped and resolved. Every diagram SKILL.md references this file instead of re-declaring the rules.

## Renderer resolution

The renderer choice is **tailored**, not hardcoded. Each skill resolves the renderer in this order:

1. `renderer_override` input parameter (explicit per-call override)
2. `pharaoh.toml` → `[pharaoh.diagrams].renderer` (project-wide default)
3. `pharaoh.toml` → `[pharaoh.diagrams.<type>].renderer` (per-diagram-type override)
4. Built-in fallback: `"mermaid"` (no JRE dependency, easiest first-time setup)

Per-type override wins over project-wide: a project can set `[pharaoh.diagrams].renderer = "mermaid"` globally but `[pharaoh.diagrams.sequence].renderer = "plantuml"` because PlantUML sequence diagrams are richer.

Supported renderers (initial set): `"mermaid"`, `"plantuml"`. Adding a third (e.g. D2, Graphviz) is a matter of adding one branch per skill; never rewrite.

## Which diagram types a project requires

A project declares which diagram types it wants in `pharaoh.toml`:

```toml
[pharaoh.diagrams]
renderer = "mermaid"
required = ["component", "sequence"]   # optional: gates pharaoh:mece or CI

# Optional per-type overrides:
[pharaoh.diagrams.component]
direction = "TB"

[pharaoh.diagrams.sequence]
renderer = "plantuml"

[pharaoh.diagrams.state]
# state-specific tailoring
```

`required` is consulted by `pharaoh-mece` / future CI skills to flag missing diagrams for features or modules. Individual diagram skills do NOT consult `required` — they emit exactly what the caller asks for.

## Node styling by need type

Optional. Lives in `pharaoh.toml`:

```toml
[pharaoh.diagrams.type_styles]
feat     = { shape = "stadium", color = "#4ECDC4" }
comp_req = { shape = "rect",    color = "#BFD8D2" }
arch     = { shape = "hexagon", color = "#F7B2B7" }
```

Each diagram skill that emits typed nodes looks up the corresponding entry and applies the renderer-specific equivalent. If absent → renderer default.

## Layout drift

Known, accepted. Mermaid's layout engine can produce non-identical output on identical input across versions, causing noisy diffs in VCS. **On this iteration we do not canonicalize output.** Users who need stable diagrams should (a) pin the renderer version, (b) commit the rendered image alongside the RST, or (c) live with diff noise. A future `pharaoh-diagram-canonicalize` skill may address this.

## check → propose → confirm (tailoring-aware skills)

Any diagram skill invoked on a project where `[pharaoh.diagrams]` is absent MUST follow the shared `check → propose → confirm` pattern (see `shared/data-access.md` for data-access flavor of the same pattern). Concretely:

1. Skill reads `pharaoh.toml`.
2. If `[pharaoh.diagrams]` is missing → emit a structured proposal in the output (not plain prose), including the default renderer choice, any per-type defaults, and a prompt for confirmation.
3. Caller (human or outer LLM) either confirms or rejects.
4. On confirm: the caller (or `pharaoh-tailor-fill`) patches `pharaoh.toml`, then re-invokes the skill with the now-present config.
5. The skill never silently picks a default on first run — the default is only "silent" on runs after the user has confirmed and the config is committed.

Parameter name for this: `on_missing_config: "fail" | "prompt" | "use_default"`, default `"prompt"`.

## Edge-handling across diagram types

Edges derive from sphinx-needs link options (`:links:`, `:satisfies:`, `:verifies:`, tailored extra links). When an edge endpoint is outside the diagram's `scope_ids`, behavior depends on diagram kind:

**Component diagrams** (`pharaoh-component-diagram-draft`): **ghost node by default.** Rendered with a distinct visual marker (dashed outline, muted color, "external" stereotype) that unambiguously separates "our scope" from "external dependencies." The diagram retains the trace information instead of hiding it. Callers who want a clean scope-only view opt out via `ghost_nodes = false` → warn + drop.

**Class diagrams** (`pharaoh-class-diagram-draft`): **FAIL on dangling.** A class diagram is a closed type model; an edge to a class not in `classes` is a caller error, not an external dependency to hint at. The caller must either add the class or remove the relationship.

**Sequence diagrams** (`pharaoh-sequence-diagram-draft`): **FAIL on dangling.** Every `from`/`to` in `messages` MUST reference an id in `participants`. External actors should be explicitly declared as `kind = "external"` participants.

**State diagrams** (`pharaoh-state-diagram-draft`): **FAIL on dangling.** Every transition endpoint MUST be a state in `states` (or `[*]`). A state machine with a transition to an undeclared state is an incomplete model, not an external dependency.

Always log a warning in addition to the default action so diffs surface the fact that "the full architecture is richer than this view" or "the caller passed an incomplete model."

Per-diagram SKILL.md re-states its dangling-edge contract to avoid ambiguity; this section is the reason WHY the contracts differ.

## What every per-type SKILL.md still has to specify

- (a) indivisibility: one diagram per call, one diagram kind, no multi-kind bundling
- (b) input contract: diagram-specific (participants+messages for sequence; classes+relationships for class; states+transitions for state; nodes+edges for component)
- (c) reward: deterministic fixture with diagram-specific validity checks (e.g. sequence must have every participant appear in at least one message; state must have exactly one initial state and at least one terminal)
- (d) reusable across projects
- (e) composable — one skill emits one block, orchestration is a caller's problem

This shared doc covers only the CROSS-CUTTING concerns (renderer, tailoring, edge handling). Per-type semantics always live in the per-type SKILL.md.

---
name: diagram
applies_to: diagram
axes:
  - trace_to_parent
  - caption_present
  - element_count_within_bounds
  - parser_clean
  - required_elements_for_type
  - conditional_branches_marked
  - external_library_participant
  - returns_match_call_stack
  - purpose_clarity
  - granularity_consistency
  - naming_clarity
---

# Diagram review checklist

Generic baseline for reviewing a single diagram block (Mermaid or PlantUML). Domain-agnostic — no references to specific standards (ISO 26262, ASPICE) or project-specific conventions (safety markers, connector-family terms, etc.). Projects add tailoring addenda.

## Mechanized axes

### trace_to_parent
Diagram's `:caption:` option OR an annotation inside the block names the parent need_id (matches regex `[A-Z_]+(__|_)[a-z0-9_]+` if the project follows sphinx-needs ID conventions). Orphan diagram (no named parent) → fail.

**Detection rule:** Extract `:caption:` value; look for the parent_need_id substring, case-sensitive. If absent, also search the diagram body for a comment or note referencing the parent.

### caption_present
The RST directive has a non-empty `:caption:` option.

**Detection rule:** grep directive options for `:caption:\s+\S`.

### element_count_within_bounds
Element count ≤ `tailoring.diagram.element_count_max` (default 7, tailorable). Element definition is renderer-specific:
- Mermaid: count of nodes (non-edge lines that introduce a new participant/node/state/class).
- PlantUML: count of `component`, `class`, `participant`, `state`, `usecase`, `rectangle` declarations.

Above the limit → fail. The >N rule signals need for decomposition.

### parser_clean
`pharaoh-diagram-lint` passes on this block. Mechanical delegation.

**Detection rule:** Run the lint atom; propagate its pass/fail.

### required_elements_for_type
Per `diagram_type`, check presence of the canonical element set declared in `pharaoh-diagram-review/SKILL.md > Per-type required-elements` table. Mechanical grep on known renderer keywords.

### conditional_branches_marked
Applies only when `diagram_type == sequence`. If the function named by `:source_doc:` contains two or more `if` / `elif` / `else` branches whose bodies produce observable calls, the diagram body must contain at least one conditional block marker. Markers are renderer-agnostic in effect: Mermaid uses `alt` / `opt` / `loop`; PlantUML uses `alt` / `opt` / `group`. Two of the three tokens (`alt`, `opt`) overlap; the detection rule looks for any of the five tokens at line-start, so both renderers are covered by the same grep.

If the source function has branching but the diagram body presents an unconditional call sequence → fail.

**Check:** source function is branching; diagram must expose that branching.

**Detection rule:** parse `:source_doc:` with the `ast` module (Python source), count `ast.If` nodes inside the named function plus any `elif`/`else` clauses they carry; if total branch count is >= 2, grep the diagram body (case-sensitive, line-start after optional whitespace) for `\b(alt|opt|loop|group)\b`. No token found → fail with evidence `"source has N conditional branches; diagram body has no alt/opt/loop/group marker"`. For non-Python sources fall back to regex `^\s*(if|elif|else\s*if|else)\b` in the function body slice delimited by the next sibling def. PlantUML-only `group` is intentionally included here and ignored for Mermaid parsing because Mermaid does not recognise `group` as a keyword — a stray `group` in Mermaid would already fail `parser_clean`, so this axis over-matches safely.

### external_library_participant
Applies to `sequence` and `block` diagrams. If the function named by `:source_doc:` imports a non-stdlib package and calls it inside the function body, the library name (or a documented alias for it) must appear as a participant in the diagram.

If an external dependency is silently elided from the interaction → fail.

**Check:** external dependencies used in the function surface as diagram participants.

**Detection rule:** parse `:source_doc:` with `ast`, collect every top-level `Import` / `ImportFrom` target whose root package is NOT a member of `sys.stdlib_module_names` (Python 3.10+) and not one of the well-known local-root markers declared in `tailoring.internal_packages` (defaults: project root package). For each such external package, confirm at least one `ast.Call` inside the named function references the imported name (attribute chain or bare name). For each confirmed external call, grep the diagram body for the library name as a participant declaration:
- Mermaid sequence: `^\s*participant\s+<lib>\b` or `^\s*<lib>\s*->>|^\s*<lib>\s*->>?\+?` (actor shorthand).
- PlantUML sequence: `^\s*(participant|actor|boundary|control|entity|database|queue|collections)\s+"?<lib>"?\b`.
- Mermaid block / flowchart: node id or label containing `<lib>` (`\b<lib>\b` anywhere in a node declaration line starting with a non-edge token).
- PlantUML block / component: `^\s*(component|rectangle|package|node|artifact)\s+"?<lib>"?\b`.

If at least one external-call library is unreferenced in the diagram body → fail with evidence `"<lib> imported and called at line N; absent from participant list"`. A single regex union `^\s*(participant|actor|component|rectangle|package|node|artifact|boundary|control|entity|database|queue|collections)\s+"?<lib>"?\b` covers both renderers' declaration forms; fall-through node-label match handles block-diagram flowchart syntax where participants are implicit.

Tailoring: `tailoring.internal_packages` (list of package roots to treat as first-party and therefore skip); `tailoring.external_alias_map` (dict from import-name to allowed diagram-label alias, e.g. `{"jira": "Jira API"}`).

### returns_match_call_stack
Applies only when `diagram_type == sequence`. Every return arrow must terminate at a participant that previously appeared as the source of a call (an entry in the live call stack) or at the diagram's declared entrypoint participant. Return arrows terminating at a free-floating participant — one that never issued a call and is not the declared entrypoint — fail the axis. Declaring `User` / `Actor` as the entrypoint is legitimate and passes; silently routing returns to an invented `User` that never called anything is the failure mode.

**Check:** return arrows respect the call stack induced by call arrows; no invented return destinations.

**Detection rule:** tokenise the diagram body line by line. For each line, classify:
- Mermaid call: `^\s*(?P<src>\w+)\s*->>\+?\s*(?P<dst>\w+)\s*:` (also `->>` without `+`).
- Mermaid return: `^\s*(?P<src>\w+)\s*-->>-?\s*(?P<dst>\w+)\s*:`.
- PlantUML call: `^\s*(?P<src>\w+)\s*->\s*(?P<dst>\w+)\s*:` (solid arrow).
- PlantUML return: `^\s*(?P<src>\w+)\s*-->\s*(?P<dst>\w+)\s*:` (dashed arrow).

Walk the token stream maintaining a stack: push `src` on every call arrow; on every return arrow check that `dst` equals either the top-of-stack caller (ideal — balanced return) OR any caller earlier on the stack (tolerated — collapsed returns) OR the declared entrypoint (first participant in `participant` / `actor` declarations, or the source of the first call). On match, pop down to that caller; on mismatch record `{"return_from": src, "return_to": dst, "stack": [...]}` in evidence and fail the axis. The entrypoint exemption ensures diagrams that legitimately start from a `User` actor pass; the stack check ensures returns to a never-seen `User` fail.

Because Mermaid's `-->>` and PlantUML's `-->` both denote returns in their respective renderers and never collide (Mermaid does not parse `-->` as a return; PlantUML does not parse `-->>` at all), the tokeniser can try both patterns in parallel and the renderer-specific grammar disambiguates by virtue of the one that matches — no explicit renderer switch needed. Lines matching neither are skipped (notes, comments, `activate` / `deactivate`, block markers handled by `conditional_branches_marked`).

## Subjective axes (0-3, LLM-judge fallback)

### purpose_clarity
- 3 — Caption + diagram together make the purpose obvious: what question does this diagram answer?
- 2 — Purpose inferrable from surrounding text.
- 1 — Purpose unclear without reading the source code.
- 0 — No identifiable purpose.

### granularity_consistency
- 3 — All elements at the same level of abstraction (e.g. all files, or all classes, not both mixed).
- 2 — One element out of level.
- 1 — Multiple levels mixed, confusing the reader.
- 0 — Level incoherent throughout.

### naming_clarity
- 3 — Every node/edge label is self-explanatory.
- 2 — One opaque label.
- 1 — Multiple opaque labels.
- 0 — Labels are meaningless or absent.

## Tailoring extension point

Per-project addenda under `.pharaoh/project/checklists/diagram.md` add axes with keys prefixed `tailoring.*`. Examples:

- Safety-critical project: `tailoring.asil_marker_present`, `tailoring.scenario_coverage` (N scenarios per dynamic view), `tailoring.supplier_manual_coverage`.
- Single-renderer project: `tailoring.renderer_is_mermaid` (project uses mermaid only), `tailoring.external_system_labelled`.

Architecture-rule examples (e.g. "every diagram must trace to requirements" → `tailoring.trace_to_requirements_full`; ">3 children requires rationale" → `tailoring.simplicity_with_rationale` parametrized with `threshold: 3`) live in project tailoring files, never in this base checklist.

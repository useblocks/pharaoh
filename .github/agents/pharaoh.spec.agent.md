---
description: Use when generating a Superpowers-compatible spec and plan document from sphinx-needs requirements, bridging requirements to implementation
handoffs:
  - label: Execute Plan
    agent: pharaoh.plan
    prompt: Execute the plan table from the generated spec
  - label: Record Decision
    agent: pharaoh.decide
    prompt: Record a design decision for a gap in the requirements
  - label: MECE Check
    agent: pharaoh.mece
    prompt: Check for traceability gaps in the spec scope
---

# @pharaoh.spec

Generate a Superpowers-compatible spec document from sphinx-needs requirements. Reads the needs hierarchy, identifies gaps, records decisions via @pharaoh.decide, and produces a markdown spec with an embedded plan table for @pharaoh.plan.

Output location: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (overridable by user).

## Data Access

1. **ubc CLI**: `ubc build needs --format json` for index, `ubc config` for schema.
2. **ubCode MCP**: Pre-indexed needs data.
3. **Raw file parsing**: Read `ubproject.toml`/`conf.py` for types, extra_links, ID settings. Grep for directives. Parse needs.

Read `pharaoh.toml` for strictness, workflow gates, traceability requirements, and `required_links` chains.

## Process

### Step 1: Get Project Data

Build needs index and full link graph (both directions for all link types). Present detection summary. If detection fails, report and ask for guidance.

### Step 2: Parse Input

Accept one or more requirement IDs. Validate against the needs index.

- **IDs not found**: Report, suggest similar IDs, ask for confirmation.
- **Natural language**: Resolve by title match, substring, content, or tags. Present candidates if multiple match.
- **Multiple IDs**: Produce a single combined spec document.

### Step 3: Resolve Requirements Scope

For each input requirement:

1. **Pull full text**: ID, title, type, status, content, tags, all links, custom fields. Requirements appear verbatim in the spec.
2. **Trace downstream**: Follow all link types recursively. Collect **references only** (ID, type, title, status, link to parent) for downstream needs.
3. **Build scope tree**: Show requirement at root with all downstream coverage and gaps.
4. **Identify gaps**: Use `required_links` chains from `pharaoh.toml` (or infer from types). Gaps: missing specs, impls, tests, or partial coverage.

### Step 4: Present Scope Summary

Show counts of requirements (full text), specs, impls, tests (references), gaps, and decisions needed. Warn if scope exceeds 30 downstream needs. Wait for user confirmation.

### Step 5: Make Design Decisions

For each gap needing a design choice (decomposition, technology, test strategy, conflicting constraints), invoke @pharaoh.decide programmatically with:

- **decided_by**: `claude`
- **status**: `accepted`
- All other fields (title, decides, alternatives, rationale) populated from context.

Write all decisions BEFORE generating the spec. The spec must reference stable decision IDs, not placeholders.

If all gaps are straightforward, skip decision recording and note it in the spec.

### Step 6: Generate the Spec Document

Write to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Create the directory if needed.

**Required sections in order**: Requirements (source of truth, full verbatim text), Existing coverage (reference table), Gaps (unchecked checkboxes), Decisions (IDs from Step 5), Implementation scope (needs to create/modify tables, "None" if empty), Plan table (built in Step 7).

Full text for requirements, ref-only for downstream. Decisions must reference stable IDs written in Step 5.

### Step 7: Build the Plan Table

Follow @pharaoh.plan task sequencing:

1. **Change analysis first** (if modifying existing needs).
2. **Author top-down**: Requirements > specs > impls > tests. New before modifications.
3. **Verify after all authoring**.
4. **MECE check** if `require_mece_on_release = true` or multi-level scope.

Each row: sequential number, concise task, exact skill name, concrete target (need ID, `(new)`, or `(all)`), specific detail, file path or `--`, and required field.

### Step 8: Handoff

Present the file path and options:

```
Spec document written to: docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md

Options:
  1. Execute the plan via @pharaoh.plan
  2. Review or modify the spec first
  3. Execute later (plan is saved in the spec document)
```

Never auto-execute. Always wait for explicit user approval.

## Strictness Behavior

**Advisory mode**: Execute freely. No gates. All plan table tasks marked `recommended`. After generating, show:
```
Tip: Consider reviewing the spec before executing the plan.
The spec captures design decisions that affect downstream authoring.
```

**Enforcing mode**: Execute freely. No gates. Plan table tasks mandated by workflow gates marked `yes`:
- `@pharaoh.change` if `require_change_analysis = true`
- `@pharaoh.verify` if `require_verification = true`
- `@pharaoh.mece` if `require_mece_on_release = true`

Both modes perform identical analysis depth. Strictness only affects the `Required` column.

## Constraints

1. **Full text for requirements, references only for downstream.** Spec is self-contained for requirements but does not duplicate downstream content.
2. **Decisions written before the spec references them.** Always invoke @pharaoh.decide first, collect the ID, then use it.
3. **Plan table format matches @pharaoh.plan exactly.** Same columns, granularity, and semantics.
4. **Never auto-execute.** Present the complete spec and wait for approval before invoking downstream skills.
5. **Single combined spec for multiple requirements.** Do not produce separate documents.
6. **No session state changes from spec generation.** Only @pharaoh.decide and @pharaoh.plan update session state.

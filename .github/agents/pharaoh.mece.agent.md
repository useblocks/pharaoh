---
description: Check for gaps, redundancies, and inconsistencies in sphinx-needs requirements. Validates traceability completeness.
handoffs:
  - label: Trace a Need
    agent: pharaoh.trace
    prompt: Trace a specific need to understand its connections
  - label: Prepare Release
    agent: pharaoh.release
    prompt: Generate release notes and changelog
---

# @pharaoh.mece -- MECE Analysis

Analyze a sphinx-needs project for structural completeness and consistency. MECE = Mutually Exclusive, Collectively Exhaustive.

**What this does:**
- **Gaps**: Finds needs missing required downstream coverage (e.g., a requirement with no specification).
- **Orphans**: Finds needs disconnected from the traceability graph.
- **Redundancy**: Flags same-type needs with very similar titles, content, or link structures.
- **Status inconsistencies**: Detects contradictions (e.g., parent closed but child still open).
- **ID violations**: Checks ID format compliance and duplicates.
- **Schema validation**: When ubc CLI is available, runs `ubc check` and `ubc schema validate`.

**Differs from @pharaoh.verify**: MECE checks structure (links, gaps, orphans). Verify checks content (does the spec actually satisfy the requirement?).

## Data Access

1. **ubc CLI**: `ubc build needs --format json`, `ubc check`, `ubc schema validate`.
2. **ubCode MCP**: Pre-indexed data with link graph.
3. **Raw file parsing**: Read config from `ubproject.toml`/`conf.py`. Grep for directives. Build needs index and link graph.

Read `pharaoh.toml` for `[pharaoh.traceability]` `required_links`. If not configured, use defaults based on detected types (e.g., `req -> spec`, `spec -> impl`, `impl -> test` if those types exist).

## Process

### Step 1: Get Project Data

Build complete needs index and link graph. Present summary:

```
Project: <name> (<config source>)
Types: <directive names>
Links: <link type names>
Data source: <tier>
Needs found: <count>
Strictness: <advisory|enforcing>
Required chains: <rules>
```

### Step 2: Gap Analysis

For each `required_links` rule (e.g., `"req -> spec"`):
1. Find all needs of the source type.
2. Check each has at least one link to a need of the target type.
3. Record gaps (source needs with no link to target type).

### Step 3: Orphan Detection

Classify each need:
- **Orphan**: No incoming AND no outgoing links. Severity: error for intermediate/leaf types, warning for root types.
- **Dead end**: Has incoming but no outgoing links. Expected for leaf types (e.g., test), error for intermediate types (e.g., spec with no impl).

Determine root/intermediate/leaf types from the `required_links` rules.

### Step 4: Redundancy Analysis

Within each need type, compare pairs for:
- **Title similarity**: Identical or near-identical titles (after normalizing case/whitespace).
- **Content similarity**: Identical content or one is a subset of the other.
- **Structural similarity**: Identical link sets (same parents AND same children).

Flag as informational. Redundancy may be intentional.

### Step 5: Status Inconsistencies

- Parent has closed-family status (`closed`, `done`, `verified`, `approved`) but child has open-family status (`open`, `draft`, `in_progress`).
- All children closed but parent still open.
- Status implies work done (e.g., `implemented`) but no link to the expected type exists.

### Step 6: ID Violations

- Check IDs match the pattern from `pharaoh.toml` `[pharaoh.id_scheme]` or the type prefix from config.
- Check for duplicate IDs across all files.
- Check format consistency within each type.

### Step 7: Schema Validation

If ubc CLI is available, run `ubc check` and `ubc schema validate`. Merge with file-based findings.

### Step 8: Present Report

```
## MECE Analysis Report

### Gaps (Missing Coverage)
| Source | Type | Missing | Required By |
|--------|------|---------|-------------|

### Orphans
| Need ID | Type | Title | Issue | Severity |
|---------|------|-------|-------|----------|

### Potential Redundancies
| Need A | Need B | Similarity | Reason |
|--------|--------|------------|--------|

### Status Inconsistencies
| Need ID | Status | Issue | Severity |
|---------|--------|-------|----------|

### ID Violations
| Need ID | Expected Pattern | Issue | Severity |
|---------|-----------------|-------|----------|

### Summary
- Gaps: <N>  Orphans: <N>  Redundancies: <N>
- Status issues: <N>  ID violations: <N>
- Overall health: <good | needs-attention | critical>
```

**Health**: good = 0 errors; needs-attention = 1-5 errors; critical = >5 errors.

### Step 9: Update Session State

Write to `.pharaoh/session.json`:
- Set `global.mece_checked = true`
- Set `global.mece_timestamp` to current timestamp.

## Scope Options

- **Full project** (default): Analyze all needs.
- **Single file/directory**: Restrict to needs in specified path. Still load full link graph for resolution.
- **Specific type**: Only analyze needs of specified type.
- **Specific chain**: Only check a specific `required_links` rule.

## Strictness Behavior

This agent has **no prerequisites**. Runs freely in any mode. Its result gates `@pharaoh.release` when `require_mece_on_release = true` in enforcing mode.

## Constraints

1. Do not skip steps. If a step produces no data, note it and continue.
2. Follow ALL configured link types. Do not hardcode type or link names.
3. Redundancy uses string comparison only, not semantic analysis.
4. Always update session state after completing the report.

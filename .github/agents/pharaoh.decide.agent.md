---
description: Use when recording a design decision as a traceable sphinx-needs object with alternatives, rationale, and links to affected requirements
handoffs:
  - label: Trace Decision
    agent: pharaoh.trace
    prompt: Trace the decision through all linked needs
  - label: Generate Spec
    agent: pharaoh.spec
    prompt: Generate a spec document from the affected requirements
---

# @pharaoh.decide

Record design decisions as `decision` needs with `decided_by`, `alternatives`, `rationale` fields and `:decides:` links. Delegates RST writing to @pharaoh.author to avoid duplicating directive-writing logic.

## Data Access

1. **ubc CLI**: `ubc build needs --format json` for index, `ubc config` for schema.
2. **ubCode MCP**: Pre-indexed needs data.
3. **Raw file parsing**: Read `ubproject.toml`/`conf.py` for types, extra_links, ID settings. Grep for directives. Parse needs.

Read `pharaoh.toml` for strictness level and workflow settings.

## Process

### Step 1: Get Project Data

Build needs index. Present detection summary. Verify that a `decision` type is configured. If missing, show the user the TOML to add:

```toml
[[needs.types]]
directive = "decision"
title = "Decision"
prefix = "DEC_"
color = "#E8D0A9"
style = "node"
```

Also verify `decided_by`, `alternatives`, `rationale` extra options and the `decides` extra link type exist. Ask user to confirm before proceeding if anything is missing.

### Step 2: Gather Decision Context

Collect all required fields:

- **Title**: What is being decided.
- **Affected needs**: Need IDs for the `:decides:` link.
- **decided_by**: Who made the decision. Default to `claude` when AI decides autonomously.
- **alternatives**: Rejected alternatives, semicolon-separated.
- **rationale**: Why this option was chosen.
- **status**: One of `proposed`, `accepted`, `superseded`, `rejected`.

**Standalone**: Prompt the user for each missing piece. Do not proceed until all five fields are populated.

**Called by @pharaoh.spec**: Accept all context programmatically. Do not prompt.

**Status defaults**: `proposed` when standalone, `accepted` when called by @pharaoh.spec. User may override.

### Step 3: Generate ID

Reuse @pharaoh.author ID generation logic:

1. Check `pharaoh.toml` for `[pharaoh.id_scheme]`. Apply pattern with `{TYPE}` resolving to `DEC`.
2. If no scheme, infer from existing `decision` needs (look for `DEC_*` numbering).
3. If no existing decisions, use prefix from type config and start at `001`, padded to `id_length`.
4. Validate uniqueness against the full needs index.

### Step 4: Write the Need

Delegate to @pharaoh.author with all fields:

```rst
.. decision:: <title>
   :id: <generated_id>
   :status: <proposed|accepted>
   :decides: <need_id1>, <need_id2>
   :decided_by: <name or claude>
   :alternatives: <alt1>; <alt2>
   :rationale: <why this option>

   <expanded description>
```

**Superseding**: When replacing an old decision, set old status to `superseded` via @pharaoh.author, add `:links: <old_dec_id>` on the new decision, and explain the replacement in the description.

### Step 5: File Placement

Place in `decisions.rst` in the same directory as the first need in `:decides:`. Create the file with proper RST title if it does not exist. If no `:decides:` links, fall back to @pharaoh.author file placement. Delegate actual writing to @pharaoh.author.

### Step 6: Update Session State

Write to `.pharaoh/session.json`: set `changes.<dec_id>.authored = true` with current ISO 8601 timestamp.

### Step 7: Follow-up

**Standalone**: Suggest `Run @pharaoh.verify to validate the decision against its linked requirements.`

**Called by @pharaoh.spec**: Return the decision ID silently. No follow-up.

## Strictness Behavior

**Advisory mode**: Execute freely. No gates. No tips needed -- decisions can be recorded at any time.

**Enforcing mode**: Execute freely. No gates. Decisions are gate-free in both modes.

Strictness has no effect on decision recording. Both modes follow the same process.

## Constraints

1. **All three fields mandatory.** Always populate `decided_by`, `alternatives`, `rationale`. Ask explicitly if any are missing.
2. **Default `decided_by` to `claude`** when the AI decides autonomously (e.g., during @pharaoh.spec).
3. **Default `status`** to `proposed` (standalone) or `accepted` (called by @pharaoh.spec).
4. **Superseding requires two writes.** Update old decision to `superseded` AND add `:links:` on the new decision.
5. **Reuse @pharaoh.author** for RST writing, file placement, and ID generation. Do not duplicate logic.
6. **Validate `:decides:` targets exist.** Warn if a target is missing from the needs index.
7. **Semicolons for alternatives.** Separate with semicolons, not commas.

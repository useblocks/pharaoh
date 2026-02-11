---
description: Create or modify sphinx-needs requirements, specifications, implementations, or test cases with proper IDs, types, attributes, and links.
handoffs:
  - label: Verify Changes
    agent: pharaoh.verify
    prompt: Verify the authored needs satisfy their parent requirements
  - label: Trace Need
    agent: pharaoh.trace
    prompt: Trace the newly authored need through all levels
---

# @pharaoh.author

AI-assisted creation and modification of sphinx-needs directives. Ensures correct RST syntax, proper IDs following the project's naming scheme, all required attributes, and valid links between needs.

## Strictness Check

**Enforcing mode** (when `pharaoh.toml` has `strictness = "enforcing"` and `require_change_analysis = true`):
1. Read `.pharaoh/session.json`.
2. For each affected need ID, verify `changes.<need_id>.acknowledged = true`.
3. If not met, block:
   ```
   Blocked: Change analysis required before authoring.
   Run @pharaoh.change for the affected requirements first.
   ```

**Advisory mode**: Execute fully. After completion, if no change analysis was done, show:
```
Tip: Consider running @pharaoh.change first to understand the impact of this modification.
```

## Data Access

1. **ubc CLI**: `ubc build needs --format json` for index, `ubc config` for schema, `ubc check` for validation.
2. **ubCode MCP**: Pre-indexed needs data.
3. **Raw file parsing**: Read `ubproject.toml`/`conf.py` for types, extra_links, ID settings. Grep for directives. Parse needs.

## Process

### Step 1: Understand the Request

Determine: create new need or modify existing? Clarify type, content, links, and file placement if ambiguous.

### Step 2: Read Project Schema

From `ubproject.toml` or `conf.py`:
- **Need types**: directive names, prefixes, titles.
- **Extra links**: option names with incoming/outgoing descriptions.
- **ID settings**: `id_required`, `id_length`.
- **Extra options**: custom metadata fields.

From `pharaoh.toml`:
- **ID scheme**: `pattern` and `auto_increment`.
- **Traceability requirements**: `required_links` (to suggest appropriate links).

### Step 3: Generate ID (for new needs)

**With pharaoh.toml id_scheme**: Parse pattern (e.g., `{TYPE}-{MODULE}-{NUMBER}`). Resolve `{TYPE}` from prefix, `{MODULE}` from context, `{NUMBER}` by auto-incrementing from highest existing.

**Without id_scheme (fallback)**: Analyze existing IDs of the same type. Detect the pattern. Increment the highest number.

**Validate uniqueness**: Ensure the generated ID doesn't already exist.

### Step 4: Create or Modify the Directive

**New need** -- generate RST:
```rst
.. <type>:: <title>
   :id: <generated_id>
   :status: open
   :tags: <tags>
   :links: <ids>
   :<extra_link>: <ids>

   <content body>
```

Formatting: 3-space indent for options and content. Blank line between options and content. Use "shall" statements for requirements.

**Modify existing** -- locate the need, make only requested changes, preserve formatting and all unchanged attributes.

### Step 5: Validate

- **Link targets**: Verify all referenced IDs exist in the needs index.
- **Link types**: Verify extra_link option names are configured.
- **ID format**: Check prefix and length compliance.
- **ubc check** (if available): Run after writing and report any issues.

### Step 6: Place in Correct File

For new needs: follow conventions (type-based files, module-based directories, same file as parent). Ask if unclear.

For modifications: use the file from the needs index.

### Step 7: Update Session State

Write to `.pharaoh/session.json`: set `changes.<need_id>.authored = true`.

Suggest next step: `Run @pharaoh.verify to validate the new/modified need.`

## Constraints

1. Validate all links before writing. Warn on non-existent targets.
2. Never fabricate need content. Use the user's description or expand minimally with confirmation.
3. Preserve existing formatting when modifying needs. Change only what was requested.
4. Use typed extra_links (`:implements:`, `:tests:`) instead of generic `:links:` when the relationship matches.
5. Always generate unique IDs. Check against the full needs index.

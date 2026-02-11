---
name: pharaoh-change
description: "Use when analyzing the impact of changing a requirement, specification, or any sphinx-needs item, including traceability to code via codelinks"
---

# pharaoh-change: Change Impact Analysis

Analyze the full impact of a proposed change to any sphinx-needs item. Trace through ALL link types -- standard `links`, `extra_links` (implements, tests, etc.), and sphinx-codelinks -- to produce a structured Change Document listing every affected need and code file with a recommended action.

This is a **gate-free skill**. It can be invoked at any time in any strictness mode. Other skills (notably `pharaoh:author`) depend on its output.

---

## 1. Understand the Change

Before accessing any project data, establish exactly what is being changed.

### Step 1a: Identify the target need(s)

Extract from the user's request:

- **Target need ID(s)**: One or more need IDs (e.g., `REQ_001`, `SPEC_002`). If the user describes the need by title or content instead of ID, note it and resolve the ID in Step 2.
- **Nature of the change**: Classify as one of:
  - **Value change** -- An attribute or content value is being modified (e.g., latency from 100ms to 50ms).
  - **Addition** -- A new attribute, link, or content section is being added to the need.
  - **Removal** -- An attribute, link, or the entire need is being removed.
  - **Restructuring** -- The need is being split, merged, or moved to a different type or module.
- **Change description**: A plain-language summary of what changes and why.

### Step 1b: Clarify ambiguity

If the user's request is ambiguous, ask exactly one round of clarifying questions before proceeding. Cover only what is missing:

- Which need ID(s) are affected?
- What specifically is changing (attribute, content, links)?
- What is the new value or desired state?

Do not ask questions whose answers can be determined from the project data.

---

## 2. Get Project Data

Follow the instructions in `skills/shared/data-access.md` to detect the project structure and build the needs index. Specifically:

1. **Detect project structure** (Section 1 of data-access.md) -- find `ubproject.toml`, `conf.py`, and the documentation source tree.
2. **Read project configuration** (Section 2) -- extract need types, link types, and ID settings.
3. **Three-tier data access** (Section 3) -- use the best available source:
   - **Tier 1: ubc CLI** -- `ubc build needs --format json` for the complete needs index.
   - **Tier 2: ubCode MCP** -- MCP tools for pre-indexed data.
   - **Tier 3: Raw file parsing** -- Grep for need directives, parse options, build the index manually.
4. **Detect sphinx-codelinks** (Section 4) -- determine if code traceability is available.
5. **Read pharaoh.toml** (Section 5) -- load strictness, workflow gates, traceability requirements, and codelinks settings.

After data access completes, present a brief detection summary:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier used>
Needs found: <count>
Codelinks: <enabled/disabled/not configured>
Strictness: <advisory/enforcing>
```

### Step 2a: Resolve need IDs from descriptions

If the user described the target need by title or content rather than ID, search the needs index now. Match by:

1. Exact title match (case-insensitive).
2. Substring match in title.
3. Substring match in content.

If multiple needs match, list them and ask the user to confirm which one(s) to analyze. If exactly one matches, proceed with it and inform the user of the resolved ID.

---

## 3. Impact Analysis

With the needs index, link graph, and target need(s) identified, perform a full impact analysis.

### Step 3a: Direct impact (one hop)

Find every need that is directly linked to ANY target need. Check all link directions:

- **Outgoing links from the target**: needs referenced in the target's `links`, `implements`, `tests`, and all other extra_link options.
- **Incoming links to the target**: needs whose `links`, `implements`, `tests`, or other extra_link options reference the target's ID.
- **Bidirectional**: For each extra_link type, check both the `outgoing` and `incoming` directions as defined in the project configuration.

For each directly linked need, record:

- Need ID
- Need type (directive name)
- Need title
- The link type connecting it to the target (e.g., `links`, `implements`, `tests`)
- The link direction (incoming or outgoing relative to the target)

### Step 3b: Transitive impact (full graph)

Starting from the set of directly impacted needs, recursively follow all links to find transitively affected needs.

**Algorithm:**

```
visited = set(target_ids)
queue = [all directly impacted needs]
distance = {direct_need: 1 for direct_need in queue}

while queue is not empty:
    current = queue.pop(0)
    for each need linked to current (all link types, both directions):
        if need.id not in visited:
            visited.add(need.id)
            distance[need.id] = distance[current.id] + 1
            queue.append(need)
```

Stop conditions:
- The queue is empty (all reachable needs have been visited).
- A configurable maximum depth has been reached (default: no limit -- traverse the entire reachable graph).

For each transitively impacted need, record:

- Need ID
- Need type
- Need title
- Distance from the target (number of hops)
- The path of link types traversed to reach it

### Step 3c: Code impact (sphinx-codelinks)

Perform this step only if sphinx-codelinks is enabled (detected in Step 2 or configured in `pharaoh.toml`).

For every need in the affected set (direct + transitive), search for code files that reference the need's ID via codelink annotations.

**Search strategy:**

1. **If ubc CLI is available**: Use ubc commands that resolve codelinks. If ubc provides a codelinks-aware query, prefer it.
2. **Raw search fallback**: Use Grep to search the project's source code directories for codelink patterns:
   - `# codelink: <NEED_ID>`
   - `// codelink: <NEED_ID>`
   - `/* codelink: <NEED_ID> */`
   - Any custom codelink pattern configured in `conf.py` or `ubproject.toml`.

Exclude documentation directories (`docs/`, `_build/`) and common non-source directories (`node_modules/`, `.git/`, `__pycache__/`).

For each code file found, record:

- File path (relative to project root)
- Line number or function/class name where the codelink appears
- The need ID it references
- Context: a brief excerpt of the surrounding code (the line containing the codelink and 2 lines above/below)

### Step 3d: Classify impact severity

For each affected item (need or code file), classify the required action:

**Must update** -- The change directly invalidates this item. Apply when:
- A specification references a specific value from the target need that is being changed (e.g., the spec mentions "100ms" and the requirement is changing to "50ms").
- A test case validates the exact property being changed (e.g., test checks response time against the old threshold).
- An implementation encodes the changed value as a constant, threshold, or parameter.
- A code file contains the changed value as a literal (found via codelinks).

**Review needed** -- The change may affect this item but requires human judgment. Apply when:
- The item is linked to the target but does not directly reference the changed value.
- The item is a sibling (e.g., another requirement linked to the same parent) that might have implicit dependencies.
- The item is transitively linked (2+ hops) and its content relates to the changed property.
- A code file references an affected need but the specific impact on the code is unclear.

**No change needed** -- The item is linked but unaffected by this specific change. Apply when:
- The item is linked to the target but addresses an entirely different property or concern.
- The item is transitively linked through a need that itself requires no change.
- The link is structural (e.g., both needs belong to the same module) but not functional.

**Classification rules:**

1. Read the content of each affected need. If the content contains the specific value being changed (e.g., "100ms", "8m/s2"), classify as "Must update".
2. If the content references the property being changed but not the specific value (e.g., "response time" without a number), classify as "Review needed".
3. If the content does not reference the changed property at all, classify as "No change needed".
4. For transitively linked needs (2+ hops), default to "Review needed" unless content analysis clearly indicates "Must update" or "No change needed".
5. For code files, default to "Review needed" unless the code contains the specific changed value as a literal.

---

## 4. Produce the Change Document

Present results in the following structured format. Use markdown tables for readability.

```
## Change Document

### Change Request
- **Target**: <NEED_ID> (<need title>)
- **Change**: <plain-language description of the change>
- **Requested by**: user
- **Date**: <current ISO 8601 date>

### Direct Impact (1 hop)

| Need ID | Type | Title | Link Type | Direction | Action |
|---------|------|-------|-----------|-----------|--------|
| <ID> | <type> | <title> | <link_type> | <in/out> | <Must update / Review needed / No change needed> |

### Transitive Impact

| Need ID | Type | Title | Distance | Path | Action |
|---------|------|-------|----------|------|--------|
| <ID> | <type> | <title> | <N hops> | <link chain> | <Must update / Review needed / No change needed> |

### Code Impact

| File | Location | Linked Need | Action |
|------|----------|-------------|--------|
| <relative path> | <function/line> | <NEED_ID> | <Must update / Review needed> |

If codelinks are not enabled or no code references are found, display:

> No code impact detected. sphinx-codelinks is not configured for this project.

or:

> No code files reference the affected needs via codelinks.

### Summary
- **Needs requiring update**: <count>
- **Needs requiring review**: <count>
- **Needs with no change needed**: <count>
- **Code files affected**: <count>
- **Total items in impact scope**: <count>
- **Maximum traversal depth**: <N hops>
- **Recommendation**: <proceed / escalate / discuss>
```

**Recommendation logic:**

- **Proceed**: 5 or fewer items require update, no safety-tagged needs are in "Must update", and the change is localized.
- **Escalate**: Any need tagged with `safety`, `critical`, or `regulatory` (or similar domain-specific tags) is classified as "Must update", OR more than 10 items require update.
- **Discuss**: The impact is ambiguous -- many items are "Review needed" with unclear severity, or the change affects needs across multiple unrelated modules.

### Multiple targets

If the user requested changes to multiple needs, produce one Change Document per target need. If the impact sets overlap, note the overlap at the end:

```
### Overlap
The following needs appear in the impact scope of multiple targets:
- <NEED_ID>: affected by both <TARGET_1> and <TARGET_2>
```

---

## 5. Update Session State

After producing the Change Document, update the session state file so other skills can check whether change analysis was performed.

Follow the session state instructions in `skills/shared/strictness.md` (Section 4).

### Step 5a: Read or initialize session state

1. Check if `.pharaoh/session.json` exists.
2. If it does not exist, create the `.pharaoh/` directory and initialize the session state:

```json
{
  "version": 1,
  "created": "<current ISO 8601 timestamp>",
  "updated": "<current ISO 8601 timestamp>",
  "changes": {},
  "global": {
    "mece_checked": false,
    "mece_timestamp": null,
    "last_release": null
  }
}
```

3. If it exists, read and parse it. If the JSON is malformed, warn the user and re-initialize.

### Step 5b: Record the change analysis

For each target need ID, add or update an entry in the `changes` dictionary:

```json
{
  "changes": {
    "<TARGET_ID>": {
      "change_analysis": "<current ISO 8601 timestamp>",
      "acknowledged": false,
      "authored": false,
      "verified": false
    }
  }
}
```

Key points:
- Set `change_analysis` to the current timestamp.
- Set `acknowledged` to `false`. The user must explicitly acknowledge before this gate is satisfied.
- Do not overwrite `authored` or `verified` if the entry already exists -- preserve those values.
- Update the top-level `updated` timestamp.

### Step 5c: Write the session state

Write the updated JSON to `.pharaoh/session.json`. Ensure the JSON is properly formatted (indented for readability).

---

## 6. Ask for Acknowledgment

After presenting the Change Document and updating session state, ask the user to acknowledge the analysis.

Present exactly this prompt:

```
Acknowledge this change analysis? Acknowledging allows proceeding to pharaoh:author for the affected needs.
```

### If the user acknowledges

Update `.pharaoh/session.json`: set `acknowledged` to `true` for each target need ID analyzed in this invocation. Update the `updated` timestamp.

Respond with:

```
Change analysis for <TARGET_ID(s)> acknowledged. You may now proceed with pharaoh:author.
```

### If the user does not acknowledge

Do not update the session state. The `acknowledged` field remains `false`.

If the user asks questions about the Change Document, answer them. If the user requests modifications to the analysis (e.g., "also check the impact on module X"), re-run the relevant parts of the analysis and present an updated Change Document. Then ask for acknowledgment again.

### If the user ignores the acknowledgment prompt

Do not force the issue. The session state remains with `acknowledged: false`. In advisory mode this has no effect. In enforcing mode, `pharaoh:author` will check and block if acknowledgment is missing.

---

## 7. Strictness Behavior

Follow the instructions in `skills/shared/strictness.md` for strictness handling. The specifics for this skill:

### Advisory mode

- Always produce the full Change Document regardless of workflow state.
- No gating -- this skill has no prerequisites.
- After completing the analysis, the acknowledgment step is optional. If the user skips it, other skills will show a tip but will not block.

### Enforcing mode

- This skill itself has no prerequisites (it is gate-free per `skills/shared/strictness.md` Section 3, "Skills with no gates").
- However, its output gates `pharaoh:author`. In enforcing mode, `pharaoh:author` checks `.pharaoh/session.json` for `acknowledged: true` on the relevant need IDs.
- Always perform the full analysis. Always update session state. Always ask for acknowledgment.

### Strictness has no effect on analysis depth

Both advisory and enforcing modes perform the same analysis. Strictness only affects whether downstream skills gate on the results.

---

## 8. Using ubc diff

If the ubc CLI is available (detected in Step 2), use `ubc diff` to supplement or replace parts of the manual impact analysis.

### When to use ubc diff

- The user is proposing a change that has already been partially implemented in the source files (e.g., they edited the RST but want to understand the impact before committing).
- The project uses version control and the user wants to compare the current state against a baseline (e.g., a branch or tag).

### How to use ubc diff

```bash
ubc diff
```

or with a specific baseline:

```bash
ubc diff --base <ref>
```

`ubc diff` returns a structured diff including:
- Which needs were added, modified, or removed.
- Which attributes changed on each need.
- Impact tracing: which linked needs are affected by each change.

### Integrating ubc diff output

If `ubc diff` provides impact tracing:
1. Use its output as the primary source for the "Direct Impact" and "Transitive Impact" sections.
2. Supplement with manual link-graph traversal only for needs or link types that ubc diff does not cover.
3. Still perform the code impact analysis (Step 3c) separately, since ubc diff may not include codelink information.
4. Still classify severity (Step 3d) using content analysis.

If `ubc diff` does not provide impact tracing (older version), use it only for identifying which needs changed, then perform the full manual analysis from Step 3.

---

## 9. Edge Cases

### Target need does not exist

If the target need ID is not found in the needs index:
1. Report that the need ID was not found.
2. Suggest possible matches (typo correction, similar IDs).
3. Ask the user to confirm or provide the correct ID.
4. Do not proceed with analysis until a valid target is identified.

### Target need has no links

If the target need has zero outgoing and zero incoming links:
1. Report that the need is an orphan (no links in any direction).
2. The Direct Impact and Transitive Impact sections are empty.
3. Still check for code impact via codelinks.
4. In the Summary, note that the change is fully isolated and recommend proceeding.

### Circular links

If the link graph contains cycles (A links to B, B links to C, C links to A):
- The traversal algorithm in Step 3b uses a `visited` set, so cycles are handled automatically.
- No need is visited twice.
- Report the cycle in the Change Document under a note:

```
Note: Circular link chain detected: <A> -> <B> -> <C> -> <A>. Each need appears once in the impact analysis.
```

### Very large impact scope

If the analysis yields more than 50 affected needs:
1. Present the full Change Document.
2. Add a warning in the Summary:

```
Warning: This change has a large impact scope (N needs). Consider breaking the change into smaller increments or reviewing the link structure for overly broad connections.
```

3. Recommend "escalate" regardless of other factors.

### Multi-project impact

If the workspace contains multiple sphinx-needs projects and the target need links to needs in a different project:
1. Identify cross-project links (need IDs that do not exist in the target's project but do exist in another project).
2. Follow the links into the other project.
3. In the Change Document, clearly mark cross-project needs:

```
| SPEC_EXT_001 | Specification | External sensor spec | 1 hop | Review needed | (project: sensor-subsystem) |
```

### Need described by title, not ID

Handled in Step 2a. If the user says "change the brake response time requirement", resolve to `REQ_001` using title matching, then proceed normally.

---

## 10. Complete Workflow Example

To illustrate the full process, here is a walkthrough using the Brake System test fixture.

**User request**: "Change REQ_001 latency from 100ms to 50ms"

**Step 1** -- Target: `REQ_001` (Brake response time). Nature: value change. Change: response time threshold from 100ms to 50ms.

**Step 2** -- Data access detects:
```
Project: Brake System (ubproject.toml)
Types: req, spec, impl, test
Links: links, implements, tests
Data source: Tier 3 (raw file parsing)
Needs found: 8
Codelinks: not configured
Strictness: advisory
```

**Step 3** -- Impact analysis:

Direct (1 hop from REQ_001):
- `SPEC_001` -- linked via `links` (incoming: SPEC_001 links to REQ_001). Content mentions "10ms signal update rate" -- related to timing. Action: **Must update** (spec for the sensor interface must reflect the tighter timing budget).
- `REQ_002` -- linked via `links` (incoming: REQ_002 links to REQ_001). Content about "force distribution" -- different property. Action: **Review needed** (sibling requirement, may have implicit timing dependency).

Transitive:
- `SPEC_002` -- 2 hops (REQ_001 -> REQ_002 -> SPEC_002 via links). Content about "force distribution algorithm". Action: **No change needed**.
- `IMPL_001` -- 2 hops (REQ_001 -> SPEC_001 -> IMPL_001 via links/implements). Content about "CAN driver for brake pedal sensor". Action: **Review needed** (driver timing may need adjustment for 50ms budget).
- `TEST_001` -- 3 hops (REQ_001 -> SPEC_001 -> IMPL_001 -> TEST_001 via links/implements/tests). Content: "Verify brake response within 100ms". Action: **Must update** (test threshold must change to 50ms).
- `IMPL_002` -- 3 hops (REQ_001 -> REQ_002 -> SPEC_002 -> IMPL_002 via links/implements). Action: **No change needed**.
- `TEST_002` -- 4 hops (via IMPL_002). Action: **No change needed**.

Code impact: Not applicable (codelinks not configured).

**Step 4** -- Change Document produced with the tables above. Summary: 2 must update, 2 review needed, 3 no change needed, 0 code files. Recommendation: proceed.

**Step 5** -- Session state written: `REQ_001` entry with `acknowledged: false`.

**Step 6** -- User asked to acknowledge. User says "yes". Session updated: `acknowledged: true`.

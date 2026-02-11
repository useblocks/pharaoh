---
name: pharaoh-trace
description: "Use when navigating traceability links between requirements, specifications, implementations, tests, and code in a sphinx-needs project"
---

# pharaoh-trace

Navigate traceability in any direction from any need in a sphinx-needs project.
Given a need ID, trace upstream to find what it satisfies and downstream to find
what satisfies it. Follow all link types: standard `links`, extra_links
(`implements`, `tests`, and any project-specific types), and sphinx-codelinks
(code-to-requirement references). Present results as a clear traceability tree
with link type labels, statuses, and gap highlights.

---

## Process

### Step 1: Get project data

Follow the instructions in `skills/shared/data-access.md` to:

1. Detect the project structure (find `ubproject.toml`, `conf.py`, source directories).
2. Read the project configuration (need types, extra_links, ID settings).
3. Determine the data access tier (ubc CLI > ubCode MCP > raw file parsing).
4. Build the needs index with all needs and their attributes.
5. Build the link graph with all relationships in both directions.
6. Detect sphinx-codelinks configuration.
7. Read `pharaoh.toml` for traceability requirements (`required_links`).

After completing data access, present the detection summary before proceeding:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier used>
Needs found: <count>
Codelinks: <enabled|not configured>
```

If detection fails (no project found, no needs in source files), report the issue
and ask the user for guidance. Do not proceed with empty data.

### Step 2: Identify the target need

The user provides either a need ID or a description.

**If the user provides a need ID** (e.g., `REQ_001`, `SPEC_002`):

1. Look up the ID in the needs index.
2. If found, confirm the target silently and proceed.
3. If not found, report the error:
   ```
   Need ID "REQ_999" not found in the project.
   Available needs with prefix REQ_: REQ_001, REQ_002, REQ_003
   ```
   Ask the user to provide a valid ID.

**If the user provides a description** (e.g., "brake response time"):

1. Search the needs index by title and content for matching terms.
2. If exactly one match is found, confirm it with the user:
   ```
   Found: REQ_001 (Requirement: Brake response time) [open]
   Proceed with tracing this need?
   ```
3. If multiple matches are found, list them and ask the user to choose:
   ```
   Multiple matches found:
   1. REQ_001 (Requirement: Brake response time) [open]
   2. SPEC_001 (Specification: Brake pedal sensor interface) [open]
   Which need should I trace? Enter the number or ID.
   ```
4. If no matches are found, report it and suggest the user check the ID or description.

**Parse optional flags from the user's input:**

- `--upstream` or `--up`: Trace only upstream (parents, what this need satisfies).
- `--downstream` or `--down`: Trace only downstream (children, what satisfies this need).
- `--depth N`: Limit recursion to N levels from the target. Default: unlimited.
- `--type <type>`: Filter the tree to show only needs of a specific type (e.g., `--type req` or `--type test`).

If no direction flag is given, trace both upstream and downstream (full trace).

### Step 3: Trace upstream (what does this need satisfy?)

Starting from the target need, follow all incoming links to find parent needs.
"Upstream" means moving toward higher-level, more abstract needs (e.g., from
a test case up to an implementation, specification, and requirement).

**Algorithm:**

```
function trace_upstream(need_id, visited, depth, max_depth):
    if need_id in visited:
        return CYCLE_DETECTED
    if max_depth is set and depth > max_depth:
        return DEPTH_LIMIT
    visited.add(need_id)

    parents = []
    # 1. Check standard links (incoming)
    for other_need in needs_index:
        if need_id in other_need.links:
            parents.append({id: other_need.id, link_type: "links"})

    # 2. Check extra_links (incoming direction)
    for link_type in project_extra_links:
        for other_need in needs_index:
            if need_id in other_need[link_type]:
                parents.append({id: other_need.id, link_type: link_type})

    # 3. Recurse for each parent
    for parent in parents:
        parent.children = trace_upstream(parent.id, visited, depth + 1, max_depth)

    return parents
```

**Key rules:**

- Follow ALL configured link types, not just the defaults. Read the project's
  `extra_links` configuration to know every valid link type name.
- For extra_links, the "incoming" direction means: find needs that have
  `:<link_type>: <target_id>` in their options. For example, if IMPL_001 has
  `:implements: SPEC_001`, then tracing upstream from IMPL_001 finds SPEC_001
  via the `implements` link type.
- For standard `links`, the direction is symmetric. If A has `:links: B`, then
  B also links to A. When tracing upstream, consider both sides.
- Track visited need IDs to detect and break cycles (see Step 3/4 cycle handling).
- Stop at the top level: needs with no incoming links (typically user stories
  or top-level requirements).

### Step 4: Trace downstream (what satisfies this need?)

Starting from the target need, follow all outgoing links to find child needs.
"Downstream" means moving toward more concrete, detailed needs (e.g., from
a requirement down to specifications, implementations, and test cases).

**Algorithm:**

```
function trace_downstream(need_id, visited, depth, max_depth):
    if need_id in visited:
        return CYCLE_DETECTED
    if max_depth is set and depth > max_depth:
        return DEPTH_LIMIT
    visited.add(need_id)

    children = []
    need = needs_index[need_id]

    # 1. Check standard links (outgoing)
    for target_id in need.links:
        children.append({id: target_id, link_type: "links"})

    # 2. Check extra_links (outgoing direction)
    for link_type in project_extra_links:
        for target_id in need[link_type]:
            children.append({id: target_id, link_type: link_type})

    # 3. Check codelinks (if enabled)
    if codelinks_enabled:
        code_refs = find_codelinks_for(need_id)
        for ref in code_refs:
            children.append({id: ref.file + ":" + ref.symbol, link_type: "codelink"})

    # 4. Recurse for each child (except codelinks, which are leaf nodes)
    for child in children:
        if child.link_type != "codelink":
            child.children = trace_downstream(child.id, visited, depth + 1, max_depth)

    return children
```

**Key rules:**

- For extra_links, the "outgoing" direction means: the target need has the link
  option set. For example, if IMPL_001 has `:implements: SPEC_001`, then tracing
  downstream from SPEC_001 finds IMPL_001 via the `implements` link (because
  IMPL_001 "implements" SPEC_001, so SPEC_001 is implemented by IMPL_001).
- Include sphinx-codelinks if enabled. Search code files for codelink annotations
  referencing the current need ID (e.g., `# codelink: REQ_001` or patterns
  defined in the codelinks configuration). Codelinks are always leaf nodes.
- Stop at leaf nodes: needs with no outgoing links (typically test cases) and
  code artifacts.

**Finding codelinks:**

If sphinx-codelinks is configured, search for code references:

1. Use Grep to search source code directories for the need ID in codelink patterns:
   ```
   Grep pattern: codelink.*<need_id>|@codelink\(.*<need_id>.*\)
   ```
2. Also check the codelinks configuration for custom patterns.
3. Each match becomes a leaf node in the downstream tree labeled `[codelink]`.

### Step 5: Handle cycles

If the traversal revisits a need ID already in the `visited` set, a cycle exists.

1. Do not recurse further into the cycle.
2. Mark the node in the output tree:
   ```
   REQ_001 (Requirement: Brake response time) [open]
   └── SPEC_001 (Specification: ...) [open] --implements-->
       └── REQ_001 [CYCLE - already visited]
   ```
3. After presenting the tree, add a warning:
   ```
   Warning: Circular link detected: SPEC_001 -> REQ_001 -> SPEC_001
   Circular links may indicate a modeling error. Review the link structure.
   ```

### Step 6: Present the traceability tree

Combine the upstream and downstream traces into a single visual tree, with the
target need as the root.

**Full trace output format (both directions):**

```
=== Traceability: REQ_001 (Requirement: Brake response time) [open] ===

--- Upstream (satisfies) ---
(no upstream links - REQ_001 is a top-level requirement)

--- Downstream (satisfied by) ---
REQ_001 (Requirement: Brake response time) [open]
├── SPEC_001 (Specification: Brake pedal sensor interface) [open] --links-->
│   ├── IMPL_001 (Implementation: Brake pedal driver) [open] --implements-->
│   │   ├── TEST_001 (Test Case: Brake response time test) [open] --tests-->
│   │   └── src/brake_controller.c:brake_check() [codelink]
│   └── [GAP] No test case directly linked to SPEC_001 (expected: spec -> impl -> test)
└── REQ_002 (Requirement: Brake force distribution) [open] --links-->
    └── SPEC_002 (Specification: Force distribution algorithm) [open] --links-->
        └── IMPL_002 (Implementation: EBD module) [open] --implements-->
            └── TEST_002 (Test Case: Force distribution test) [open] --tests-->
```

**Upstream-only output format** (when `--upstream` is used):

```
=== Upstream trace from IMPL_001 (Implementation: Brake pedal driver) [open] ===

IMPL_001 (Implementation: Brake pedal driver) [open]
└── SPEC_001 (Specification: Brake pedal sensor interface) [open] --implements-->
    └── REQ_001 (Requirement: Brake response time) [open] --links-->
        (top-level requirement - no further upstream links)
```

**Downstream-only output format** (when `--downstream` is used):

```
=== Downstream trace from REQ_001 (Requirement: Brake response time) [open] ===

REQ_001 (Requirement: Brake response time) [open]
├── SPEC_001 (Specification: Brake pedal sensor interface) [open] --links-->
│   └── IMPL_001 (Implementation: Brake pedal driver) [open] --implements-->
│       └── TEST_001 (Test Case: Brake response time test) [open] --tests-->
└── REQ_002 (Requirement: Brake force distribution) [open] --links-->
    └── ...
```

**Tree formatting rules:**

- Each node shows: `ID (Type: Title) [status]`
- After each node, show the link type label that connects it to its parent: `--<link_type>-->`
- Use box-drawing characters for the tree structure: `├──`, `└──`, `│`
- Indent each level by 4 characters.
- For codelinks, show: `file:symbol [codelink]`
- For cycle nodes, show: `ID [CYCLE - already visited]`
- For depth-limited nodes, show: `... (depth limit reached)`

### Step 7: Highlight gaps

After building the tree, check for traceability gaps using the `required_links`
from `pharaoh.toml` (if configured).

**Gap detection logic:**

For each `required_links` entry (e.g., `"req -> spec"`):

1. Find all needs of the source type (e.g., all `req` needs).
2. For each source need, check if it has at least one downstream link to a need
   of the target type (e.g., at least one `spec`).
3. If no link exists, this is a gap.

Only report gaps that are visible in the current trace (needs that appear in the
tree but are missing expected children). Do not report gaps for needs outside the
trace scope.

**Gap display:**

Insert gap markers directly into the tree where expected children are missing:

```
REQ_003 (Requirement: Emergency brake activation) [open]
└── SPEC_003 (Specification: Emergency detection logic) [open] --links-->
    └── [GAP] No implementation linked (expected: spec -> impl)
```

After the tree, provide a gap summary:

```
Traceability gaps found: 2
- SPEC_003: Missing implementation (required: spec -> impl)
- REQ_003: No test coverage through full chain (req -> spec -> impl -> test)

Tip: Run pharaoh:author to create the missing needs, or pharaoh:mece for a full gap analysis.
```

If no `required_links` are configured in `pharaoh.toml`, skip gap detection and
do not show gap markers. Mention this:

```
Note: No required_links configured in pharaoh.toml. Gap detection is disabled.
Configure [pharaoh.traceability] required_links to enable gap highlighting.
```

### Step 8: Filtered views

Apply filters based on the user's flags before presenting the tree.

**Type filter** (`--type <type>`):

When `--type` is specified, prune the tree to show only the path from the target
need to needs of the specified type. Intermediate needs on the path are shown
but visually de-emphasized:

```
=== Trace REQ_001 -> test (filtered) ===

REQ_001 (Requirement: Brake response time) [open]
  via SPEC_001 -> IMPL_001
    └── TEST_001 (Test Case: Brake response time test) [open]
  via SPEC_002 -> IMPL_002
    └── TEST_002 (Test Case: Force distribution test) [open]
```

**Depth limit** (`--depth N`):

When `--depth` is specified, stop recursion at N levels. Show a truncation
marker at the depth boundary:

```
REQ_001 (Requirement: Brake response time) [open]
├── SPEC_001 (Specification: Brake pedal sensor interface) [open] --links-->
│   └── ... (depth limit: 1)
└── REQ_002 (Requirement: Brake force distribution) [open] --links-->
    └── ... (depth limit: 1)
```

### Step 9: Multi-project support

In multi-project setups (multiple `ubproject.toml` files detected):

1. Build a needs index for each project separately.
2. When tracing, if a link target ID is not found in the current project, search
   other project indexes.
3. When a cross-project link is found, annotate it in the tree:
   ```
   SPEC_EXT_001 (Specification: External interface) [open] [project: sensor-system]
   ```
4. If a linked ID is not found in any project, mark it:
   ```
   SPEC_UNKNOWN (not found in any project)
   ```

Also check for external needs imported via `needs_external_needs` or
`needs_from_toml` external references. These are needs defined outside the
current source tree but imported into the build.

---

## Constraints

1. **Handle circular links gracefully.** Always use a visited set during traversal.
   Never enter infinite recursion. Report cycles clearly to the user.

2. **Support all configured link types.** Read the project's `extra_links`
   configuration and follow every defined link type. Do not hardcode link type
   names like `implements` or `tests`. The project may define custom link types
   such as `satisfies`, `derives_from`, `blocks`, `validates`, or any other name.

3. **Always show link type labels.** Every edge in the tree must show how the
   two needs are connected (e.g., `--implements-->`, `--tests-->`, `--links-->`).
   This is critical for understanding the nature of each relationship.

4. **Show status on every node.** The status value (e.g., `open`, `in_progress`,
   `closed`, `approved`) helps the user understand the maturity of the trace chain.

5. **Work with incomplete data.** If a linked ID does not exist in the needs index,
   show it as a broken reference rather than silently dropping it:
   ```
   IMPL_999 [BROKEN LINK - need not found]
   ```

6. **No session state changes.** This skill is read-only. It does not modify
   `.pharaoh/session.json` or any project files. It only reads and presents data.

7. **No workflow gates.** As noted in `skills/shared/strictness.md`, `pharaoh:trace`
   has no prerequisites and executes freely in both advisory and enforcing modes.

8. **Performance on large projects.** If the needs index contains more than 500
   needs, warn the user that a full bidirectional trace may produce a large tree
   and suggest using `--depth` or `--type` filters:
   ```
   Note: Project contains 1,247 needs. Consider using --depth or --type to limit output.
   Proceeding with full trace...
   ```

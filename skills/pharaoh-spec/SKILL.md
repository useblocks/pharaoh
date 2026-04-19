---
name: pharaoh-spec
description: "Use when generating a Superpowers-compatible spec and plan document from sphinx-needs requirements, bridging requirements to implementation"
---

# pharaoh-spec

Generate a self-contained specification and plan document from one or more sphinx-needs
requirements. The spec bridges the gap between requirements (the "what") and
implementation (the "how") by pulling full requirement text, mapping existing downstream
coverage, identifying gaps, recording design decisions via `pharaoh:decide`, and
producing a plan table that feeds directly into `pharaoh:plan`.

The output is a markdown document in `docs/superpowers/specs/` containing requirements,
coverage analysis, gap list, decisions, and an actionable plan table.

## When to Use

- You have one or more requirement IDs and need a structured spec before implementation begins.
- You want to understand what downstream coverage already exists for a set of requirements (specs, impls, tests) and what gaps remain.
- You need to record design decisions for uncovered areas before authoring new needs.
- You want a single document that a team can review before executing changes via `pharaoh:plan`.
- A new feature has been captured as requirements and you need to decompose it into specifications, implementations, and test cases with full traceability.

## Prerequisites

- The workspace must contain at least one sphinx-needs project.
- No workflow gates. This skill runs freely in both advisory and enforcing modes.
- If decisions need to be recorded, the project must have a `decision` type configured (see `pharaoh:decide` Step 1).

---

## Process

Execute the following steps in order.

---

### Step 1: Get Project Data

Follow the full detection and data access algorithm defined in `skills/shared/data-access.md`.

1. Detect project structure (project roots, source directories, configuration).
2. Read project configuration (need types, link types, ID settings).
3. Build the needs index using the best available data tier (ubc CLI, ubCode MCP, or raw file parsing).
4. Build the link graph with all relationships in both directions (outgoing and incoming for every link type including extra_links).
5. Read `pharaoh.toml` for strictness level, workflow gates, traceability requirements, and `required_links` chains.

Present the detection summary before proceeding:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier used>
Needs found: <count>
Strictness: <advisory|enforcing>
```

If detection fails (no project found, no needs in source files), report the issue and ask the user for guidance. Do not proceed with empty data.

---

### Step 2: Parse Input

Accept one or more requirement IDs from the user's request.

#### When the user provides IDs directly

Validate each ID against the needs index. If an ID does not exist:

1. Report that the ID was not found.
2. Suggest possible matches (typo correction, similar IDs).
3. Ask the user to confirm or provide the correct ID.

#### When the user provides natural language

Resolve to IDs using the needs index. Match by:

1. Exact title match (case-insensitive).
2. Substring match in title.
3. Substring match in content.
4. Tag match.

If multiple needs match, present candidates and ask the user to choose:

```
Multiple matches found:
1. REQ_001 (Requirement: Brake response time) [open]
2. REQ_007 (Requirement: Brake pedal response) [approved]
Which requirement(s) should be included in the spec? Enter numbers or IDs.
```

If exactly one matches, proceed with it and inform the user of the resolved ID.

#### Multiple requirements

When called with multiple requirement IDs, produce a single combined spec document covering all of them. Do not produce separate documents per requirement.

---

### Step 3: Resolve Requirements Scope

For each input requirement, build a complete scope tree.

#### 3a: Pull full requirement text

For each input requirement, retrieve all available fields:

- ID, title, type, status
- Full content text
- Tags
- All link fields (links, implements, tests, and any extra_links)
- Any custom fields defined in the project configuration

This is the **full text** -- requirements are the source of truth and must appear verbatim in the spec document.

#### 3b: Trace downstream coverage

Starting from each input requirement, follow the link graph recursively to find all downstream needs. Follow all link types (links, implements, tests, and all extra_links) in both directions. Continue until the full downstream tree is mapped.

For each downstream need, collect **references only** (ID, type, title, status, link type to parent). Do NOT pull full content for downstream needs -- they are resolvable via `ubc` or source files if needed later.

#### 3c: Build the scope tree

Assemble a tree showing the requirement at the root with all downstream coverage:

```
REQ_042 (full text)
+-- SPEC_010 (ref) -- exists, status: open
+-- SPEC_011 (ref) -- exists, status: approved
|   +-- IMPL_005 (ref) -- exists, status: open
+-- [gap] -- no spec covers subsystem X
    +-- [gap] -- no impl for subsystem X
        +-- [gap] -- no test for subsystem X
```

#### 3d: Identify gaps

Determine what downstream coverage is missing using `pharaoh.toml` `required_links` chains. If `required_links` is configured, follow the chain (e.g., `req -> spec -> impl -> test`). If not configured, infer expected chains from configured types and link types.

Gaps include: requirements with no spec, specs with no impl, impls with no test, and requirements whose content suggests multiple subsystems with only partial spec coverage.

For each gap, record the parent need ID, what is missing, and whether it represents a decision point (ambiguity in decomposition or approach).

---

### Step 4: Present Scope Summary

Before generating the spec document, present a summary for the user to review:

```
Scope for REQ_042:
  Requirements: 1 (full text included)
  Specifications: 2 (references only)
  Implementations: 1 (reference only)
  Test cases: 0
  Gaps: 2 (no spec for subsystem X, no test for IMPL_005)
  Decisions needed: 2
```

For multiple requirements, show a combined summary with the same format.

If the scope is unexpectedly large (more than 30 downstream needs), warn the user and suggest splitting into separate specs per requirement.

Wait for user confirmation before proceeding to Step 5.

---

### Step 5: Make Design Decisions

For each gap or ambiguity identified in Step 3d, determine whether a design decision is needed.

#### When decisions are needed

Decisions are needed when:

- **Missing spec coverage**: How should the requirement be decomposed into specifications? What design approach should be taken?
- **Multiple implementation approaches**: Which technology, algorithm, or architecture should be used?
- **Missing test coverage**: What verification method is appropriate (unit test, integration test, manual review)?
- **Conflicting constraints**: Two requirements impose contradictory constraints on a shared specification.

#### Recording decisions

For each decision, invoke `pharaoh:decide` programmatically with all context:

- **Title**: A clear statement of the decision (e.g., "Decompose REQ_042 into timing and protocol specifications").
- **decides**: The need IDs affected by this decision.
- **decided_by**: `claude` (since the AI is generating the spec).
- **alternatives**: At least two alternatives considered, semicolon-separated.
- **rationale**: Why this option was chosen.
- **status**: `accepted` (decisions made during spec generation are accepted by default).

`pharaoh:decide` will generate the decision ID, write the RST directive, and return the ID. Collect all decision IDs for use in Step 6.

**Important**: Write all decisions BEFORE generating the spec document. The spec must reference stable decision IDs, not placeholders.

#### When no decisions are needed

If all gaps are straightforward (e.g., a missing test case for an existing implementation where the test strategy is obvious), skip decision recording. Note in the spec that no design decisions were required.

---

### Step 6: Generate the Spec Document

Write the spec document to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.

- `YYYY-MM-DD` is the current date.
- `<topic>` is a short kebab-case slug derived from the requirement title(s) (e.g., `brake-response-time`).
- The user may override the file path. If they specify a different location, use it.

Create the `docs/superpowers/specs/` directory if it does not exist.

#### Document structure

The spec document MUST contain these sections in this order:

```markdown
# Spec: <Requirement title(s)>

Generated from sphinx-needs on YYYY-MM-DD.
Source requirements: REQ_042, REQ_043

## Requirements (source of truth)

### REQ_042: <title>
**Status:** <status> | **Tags:** <tag1>; <tag2>

<Full requirement content text pulled verbatim from sphinx-needs.>

### REQ_043: <title>
**Status:** <status> | **Tags:** <tag1>; <tag2>

<Full requirement content text pulled verbatim from sphinx-needs.>

## Existing coverage

| Need | Type | Title | Status | Links |
|------|------|-------|--------|-------|
| SPEC_010 | spec | Signal timing | open | REQ_042 |
| SPEC_011 | spec | Protocol design | approved | REQ_042 |
| IMPL_005 | impl | CAN driver | open | SPEC_011 |

## Gaps

- [ ] No specification covers subsystem X of REQ_042
- [ ] No test case for IMPL_005
- [ ] No implementation for SPEC_010

## Decisions

- DEC_001: Decompose REQ_042 into timing and protocol specifications
- DEC_002: Use CAN bus for sensor communication

> If no decisions were needed, write: "No design decisions required. All gaps are
> covered by straightforward additions."

## Implementation scope

### Needs to create
| Type | Purpose | Links to | File |
|------|---------|----------|------|
| spec | Subsystem X timing | REQ_042 | specifications.rst |
| test | CAN driver verification | IMPL_005 | test_cases.rst |

### Needs to modify
| Need | Change | Reason |
|------|--------|--------|
| SPEC_010 | Update timing constraints | REQ_042 timing budget changed |

> If no needs to create or modify, write "None" for the respective subsection.

## Plan table

| # | Task | Skill | Target | Detail | File | Required |
|---|------|-------|--------|--------|------|----------|
| 1 | Analyze impact | pharaoh:change | REQ_042 | Trace downstream effects | docs/requirements.rst | yes |
| 2 | Author spec | pharaoh:req-draft | (new) | Subsystem X timing | docs/specifications.rst | yes |
| 3 | Author test | pharaoh:req-draft | (new) | CAN driver verification | docs/test_cases.rst | yes |
| 4 | Update spec | pharaoh:req-draft | SPEC_010 | Timing constraints | docs/specifications.rst | yes |
| 5 | Verify | pharaoh:req-review | (all) | Check traceability | -- | yes |
```

#### Section rules

1. **Requirements**: Full verbatim text. The spec must be self-contained for requirement content.
2. **Existing coverage**: Reference table only, sorted by type (specs, impls, tests).
3. **Gaps**: Checkbox list (unchecked). One item per gap from Step 3d.
4. **Decisions**: List each by ID and title, referencing the decision need written in Step 5.
5. **Implementation scope**: "Needs to create" (with suggested target files) and "Needs to modify" (with change description and reason). Write "None" if a subsection is empty.
6. **Plan table**: Built in Step 7. Same columns and format as `pharaoh:plan` Step 5.

---

### Step 7: Build the Plan Table

Construct the plan table following `pharaoh:plan` task sequencing rules.

#### Task ordering

1. **Change analysis first** (if modifying existing needs): One `pharaoh:change` task per modified need, or a single task covering all modifications.
2. **Author needs top-down**: Requirements before specifications, specifications before implementations, implementations before test cases. New needs before modifications at each level.
3. **Verify after all authoring**: One review skill task (e.g. `pharaoh:req-review`) covering all created and modified needs.
4. **MECE check if configured**: Include a `pharaoh:mece` task if `require_mece_on_release = true` in `pharaoh.toml`, or if the scope involves creating needs at multiple hierarchy levels.

#### Task format

Each task row must specify:

- **#**: Sequential number starting from 1.
- **Task**: Concise description of what the task does.
- **Skill**: The exact Pharaoh skill to invoke (e.g., `pharaoh:change`, `pharaoh:req-draft`, `pharaoh:req-review`, `pharaoh:mece`).
- **Target**: The need ID being acted on, or `(new)` for needs to create, or `(all)` for verification tasks.
- **Detail**: A specific description of the change or action. Not vague -- name the exact property or content being changed.
- **File**: The target file path for the task (e.g., `docs/requirements.rst`, `docs/specifications.rst`), or `--` if not applicable.
- **Required**: `yes`, `no`, or `recommended` based on strictness mode.

#### Required field rules

- **Enforcing mode**: Tasks mandated by workflow gates are marked `yes`. Optional tasks (like MECE check when not required) are marked `recommended`.
- **Advisory mode**: All tasks are marked `recommended`. No task is strictly required.

#### Plan table constraints

- The plan table MUST use the exact same format and column names as `pharaoh:plan` Step 5. This ensures the plan can be handed off to `pharaoh:plan` for execution without reformatting.
- One skill invocation per task. Do not combine multiple skill calls into a single row.
- Every task must have a concrete target. Vague tasks like "update related specs" are not acceptable.

---

### Step 8: Handoff

After generating the spec document, present the file path and offer next steps:

```
Spec document written to: docs/superpowers/specs/2026-04-07-brake-response-time-design.md

Options:
  1. Execute the plan via pharaoh:plan
  2. Review or modify the spec first
  3. Execute later (plan is saved in the spec document)
```

- **Option 1**: Invoke `pharaoh:plan` with the plan table from the spec document.
- **Option 2**: Allow edits to any section, regenerate affected parts, then re-offer options.
- **Option 3**: Confirm the spec is saved. No further action.

**Never auto-execute.** Always present the spec and wait for explicit user approval.

---

## Strictness Behavior

Follow the instructions in `skills/shared/strictness.md`.

### Advisory mode

- Execute freely. No gates. This skill has no prerequisites.
- All plan table tasks are marked `recommended` instead of `yes`.
- Decisions are still recorded (they provide traceability regardless of strictness).
- After generating the spec, show a tip if the user skips review:
  ```
  Tip: Consider reviewing the spec before executing the plan.
  The spec captures design decisions that affect downstream authoring.
  ```

### Enforcing mode

- Execute freely. No gates. This skill has no prerequisites.
- Plan table tasks mandated by workflow gates are marked `yes`:
  - `pharaoh:change` tasks are required if `require_change_analysis = true`.
  - review skill tasks are required if `require_verification = true`.
  - `pharaoh:mece` tasks are required if `require_mece_on_release = true`.
- Decisions are recorded with status `accepted` (same as advisory mode).
- The spec document clearly marks which plan tasks are mandatory.

### Strictness has no effect on analysis depth

Both advisory and enforcing modes perform the same scope resolution, gap analysis, and decision recording. Strictness only affects the `Required` column in the plan table and whether downstream skills gate on prerequisites.

---

## Key Constraints

1. **Requirements get full text, downstream needs get references only.** The spec is self-contained for requirements but does not duplicate downstream content. Downstream details are resolvable via `ubc` or by reading source files.

2. **Decisions are written as sphinx-needs objects before the spec references them.** Never reference a decision ID that has not been written. Always invoke `pharaoh:decide` first, collect the ID, then use it in the spec.

3. **Plan table format must match `pharaoh:plan` exactly.** Same column names, same task granularity, same required-field semantics. The plan table in the spec must be directly executable by `pharaoh:plan`.

4. **Spec doc location defaults to `docs/superpowers/specs/` but is overridable.** If the user specifies a different path, use it without question.

5. **Never auto-execute.** Always present the complete spec document and wait for explicit user approval before invoking any downstream skill. This applies even if the plan has only one task.

6. **When called with multiple requirement IDs, produce a single combined spec.** Do not generate separate documents per requirement. The scope tree, gap analysis, and plan table cover all input requirements together.

7. **Keep the spec document focused.** Do not include implementation details, code snippets, or design elaborations beyond what the decisions capture. The spec is a bridge document -- it connects requirements to a plan, not a detailed design document.

8. **No session state changes from spec generation alone.** Generating and writing the spec document does not modify `.pharaoh/session.json`. Only decision recording (via `pharaoh:decide`) and plan execution (via `pharaoh:plan`) update session state.

---

## Examples

### Example 1: Single requirement with gaps

**User request**: `pharaoh:spec REQ_001`

**Step 1** -- Data access detects:

```
Project: Brake System (ubproject.toml)
Types: req, spec, impl, test, decision
Links: links, implements, tests, decides
Data source: Tier 3 (raw file parsing)
Needs found: 12
Strictness: advisory
```

**Step 2** -- Input: `REQ_001`. Validated against needs index. Found: `REQ_001` (Brake response time).

**Step 3** -- Scope resolution:

Full text retrieved for REQ_001:
- Title: "Brake response time"
- Status: approved
- Tags: safety; braking
- Content: "The brake system shall respond within 100ms of pedal input under all operating conditions."

Downstream trace:
```
REQ_001 (full text)
+-- SPEC_001 (ref) -- Signal timing, status: open
|   +-- IMPL_001 (ref) -- CAN driver, status: open
+-- [gap] -- no spec for subsystem X (pedal sensor interface)
    +-- [gap] -- no impl
        +-- [gap] -- no test
+-- [gap] -- no test for IMPL_001
```

Gaps identified:
1. No specification covers the pedal sensor interface subsystem.
2. No test case for IMPL_001 (CAN driver).

**Step 4** -- Scope summary presented:

```
Scope for REQ_001:
  Requirements: 1 (full text included)
  Specifications: 1 (reference only)
  Implementations: 1 (reference only)
  Test cases: 0
  Gaps: 2 (no spec for pedal sensor interface, no test for IMPL_001)
  Decisions needed: 2
```

User confirms: proceed.

**Step 5** -- Decisions recorded via `pharaoh:decide`:

1. `DEC_003`: "Decompose pedal sensor interface into separate specification"
   - decides: REQ_001
   - alternatives: Include in SPEC_001; Create standalone spec
   - rationale: Pedal sensor interface is safety-critical and warrants independent review
   - Result: DEC_003 written to decisions.rst

2. `DEC_004`: "Use hardware-in-the-loop testing for CAN driver verification"
   - decides: IMPL_001
   - alternatives: Unit test with mock CAN; HIL testing; Manual bench test
   - rationale: Safety-critical braking path requires realistic signal conditions
   - Result: DEC_004 written to decisions.rst

**Step 6** -- Spec document generated at `docs/superpowers/specs/2026-04-07-brake-response-time-design.md` with:
- Full text of REQ_001 in Requirements section
- Coverage table: SPEC_001 (open), IMPL_001 (open)
- Gaps: no spec for pedal sensor interface, no test for IMPL_001
- Decisions: DEC_003, DEC_004
- Implementation scope: create 1 spec (pedal sensor timing) and 1 test (CAN driver HIL)
- Plan table (advisory mode, all `recommended`):

| # | Task | Skill | Target | Detail | File | Required |
|---|------|-------|--------|--------|------|----------|
| 1 | Analyze impact | pharaoh:change | REQ_001 | Trace downstream effects of new spec | docs/requirements.rst | recommended |
| 2 | Author spec | pharaoh:req-draft | (new) | Pedal sensor interface timing spec | docs/specifications.rst | recommended |
| 3 | Author test | pharaoh:req-draft | (new) | CAN driver HIL test case | docs/test_cases.rst | recommended |
| 4 | Verify coverage | pharaoh:req-review | (all) | Check REQ_001 traceability chain | -- | recommended |

**Step 8** -- Handoff:

```
Spec document written to: docs/superpowers/specs/2026-04-07-brake-response-time-design.md

Options:
  1. Execute the plan via pharaoh:plan
  2. Review or modify the spec first
  3. Execute later (plan is saved in the spec document)
```

---

### Example 2: Multiple requirements, full coverage

**User request**: `pharaoh:spec REQ_001 REQ_002`

**Step 1** -- Same detection as Example 1.

**Steps 2-3** -- Both IDs validated. Scope resolution finds full downstream coverage for both requirements (each has spec, impl, and test in approved status). No gaps, no decisions needed.

**Step 4** -- Scope summary:

```
Scope for REQ_001, REQ_002:
  Requirements: 2 (full text included)
  Specifications: 2 (references only)
  Implementations: 2 (references only)
  Test cases: 2 (references only)
  Gaps: 0
  Decisions needed: 0
```

**Steps 5-6** -- Decisions skipped. Spec document generated at `docs/superpowers/specs/2026-04-07-brake-system-design.md` with both requirements in full text, a complete coverage table (6 downstream needs), empty gaps section ("No gaps identified"), empty decisions section, and no plan table ("No tasks required. All requirements have complete traceability chains.").

**Step 8** -- Handoff offers: review the spec, run `pharaoh:req-review` to confirm traceability, or done.

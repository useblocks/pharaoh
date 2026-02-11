---
name: pharaoh-plan
description: "Use when breaking requirement changes into structured implementation tasks with workflow enforcement and dependency ordering"
---

# pharaoh-plan

Break a set of requirement changes into ordered, actionable tasks. Each task maps
to a Pharaoh skill invocation. The plan respects `pharaoh.toml` workflow gates,
establishes task dependencies, and provides a roadmap for implementing changes
across the requirements hierarchy.

## When to Use

- A requirement needs to change and you want a structured sequence of steps to propagate that change through specifications, implementations, and test cases.
- A new feature is being added and you need to create needs at every level of the hierarchy with proper traceability.
- Multiple requirements are changing at once and you need to coordinate the work.
- You have a Change Document from `pharaoh:change` and want to turn its impact analysis into an execution plan.
- You want to ensure workflow compliance (change analysis before authoring, verification before release) without manually tracking what has been done.

## Prerequisites

- The workspace must contain at least one sphinx-needs project.
- No other Pharaoh skills are required before running this one. `pharaoh:plan` has no workflow gates and runs freely in both advisory and enforcing modes.

---

## Process

Execute the following steps in order.

---

### Step 1: Get project data

Follow the instructions in `skills/shared/data-access.md` to:

1. Detect the project structure (find `ubproject.toml`, `conf.py`, source directories).
2. Read the project configuration (need types, extra_links, ID settings).
3. Determine the data access tier (ubc CLI > ubCode MCP > raw file parsing).
4. Build the needs index with all needs and their attributes.
5. Build the link graph with all relationships in both directions.
6. Detect sphinx-codelinks configuration.
7. Read `pharaoh.toml` for strictness level, workflow gates, and traceability requirements.

After completing data access, present the detection summary before proceeding:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier used>
Needs found: <count>
Strictness: <advisory|enforcing>
```

If detection fails (no project found, no needs in source files), report the issue
and ask the user for guidance. Do not proceed with empty data.

---

### Step 2: Understand the scope

Determine what changes the user wants to make.

**If the user provides a Change Document** (output from a previous `pharaoh:change` invocation):

1. Parse the Change Document to extract:
   - The target need ID(s) and what is changing.
   - The list of affected needs (downstream impacts).
   - The affected files.
2. Use this as the authoritative scope. Do not re-run change analysis.

**If the user describes the change in natural language** (e.g., "change brake response time from 100ms to 50ms"):

1. Identify which need(s) the user is referring to. Search the needs index by title, content, and tags.
2. If the target need is ambiguous, present candidates and ask the user to choose:
   ```
   Multiple matches found:
   1. REQ_001 (Requirement: Brake response time) [open]
   2. REQ_007 (Requirement: Brake pedal response) [approved]
   Which need(s) are you changing? Enter numbers or IDs.
   ```
3. Once the target is confirmed, determine the scope by running the `pharaoh:change` impact analysis logic:
   - Trace downstream from each target need to find all affected specifications, implementations, test cases, and code references.
   - Record every affected need with its type, file, and the nature of the expected change.

**If the user wants to add a new feature** (no existing need to change):

1. Confirm what the feature is and which levels of the hierarchy need new needs (requirements, specifications, implementations, test cases).
2. The scope is "create new" rather than "modify existing." There are no affected needs yet, only needs to be created.
3. Determine how many needs are expected at each level based on the feature description and the project's traceability requirements (`required_links` from `pharaoh.toml`).

**Scope summary:**

After determining the scope, record:
- **Change type**: `modify` (changing existing needs) or `create` (adding new needs).
- **Target needs**: The need ID(s) being changed or the description of new needs to create.
- **Affected needs**: All needs that must be updated as a consequence (for `modify` type).
- **Affected files**: The source files that contain the target and affected needs.
- **Hierarchy levels touched**: Which need types are involved (e.g., req, spec, impl, test).

---

### Step 3: Read workflow gates

Follow the instructions in `skills/shared/strictness.md` to determine which workflow gates apply.

Read `pharaoh.toml` (or use defaults if absent):

- `strictness`: `"advisory"` or `"enforcing"`.
- `require_change_analysis`: Whether `pharaoh:author` requires a prior `pharaoh:change`.
- `require_verification`: Whether `pharaoh:release` requires a prior `pharaoh:verify`.
- `require_mece_on_release`: Whether `pharaoh:release` requires a prior `pharaoh:mece`.

These gates determine which tasks are mandatory in the plan versus optional.

---

### Step 4: Build the task sequence

Assemble the ordered list of tasks based on the scope and workflow gates.

#### Task sequence for modifying existing needs

When the change type is `modify`, use this default sequence:

1. **Change analysis** (`pharaoh:change`): Analyze impact of the change on the target need(s). Produces a Change Document listing all affected needs.
   - Skip this task if the user already provided a Change Document.
   - In enforcing mode with `require_change_analysis = true`, this task is mandatory before any authoring tasks.

2. **Author target need(s)** (`pharaoh:author`): Modify each target need with the requested change. One task per target need.

3. **Author affected specifications** (`pharaoh:author`): Update each specification that traces to a modified need. One task per affected specification.

4. **Author affected implementations** (`pharaoh:author`): Update each implementation that traces to a modified specification. One task per affected implementation.

5. **Author affected test cases** (`pharaoh:author`): Update each test case that traces to a modified implementation. One task per affected test case.

6. **Verify all changes** (`pharaoh:verify`): Verify that all modified needs satisfy their parents and meet traceability requirements.
   - In enforcing mode with `require_verification = true`, this task is mandatory before any release task.

7. **MECE check** (`pharaoh:mece`): Check for gaps, redundancies, or inconsistencies introduced by the changes. This task is optional by default.
   - In enforcing mode with `require_mece_on_release = true`, this task is mandatory before any release task.

8. **Release** (`pharaoh:release`): Generate a changelog entry for the changes. Include this task only if the user indicates they are preparing a release.

**Ordering within authoring tasks**: Follow the hierarchy top-down. Modify needs in this order: requirements first, then specifications, then implementations, then test cases. This ensures that each level is updated before its children are modified, so authors can reference the updated parent content.

#### Task sequence for adding new needs

When the change type is `create`, use this sequence:

1. **Author new requirement(s)** (`pharaoh:author`): Create the new top-level requirement(s). One task per requirement.

2. **Author new specifications** (`pharaoh:author`): Create specifications for each new requirement. One task per specification.

3. **Author new implementations** (`pharaoh:author`): Create implementations for each new specification. One task per implementation.

4. **Author new test cases** (`pharaoh:author`): Create test cases for each new implementation. One task per test case.

5. **MECE check** (`pharaoh:mece`): Verify complete coverage across the new needs. Confirm that every `required_links` chain is satisfied.

6. **Verify all new needs** (`pharaoh:verify`): Verify that all new needs have proper links and satisfy their parents.

**Note on hierarchy levels**: Not every project uses all four levels (req, spec, impl, test). Only include tasks for need types that exist in the project's configuration. If the project defines only `req` and `test`, the plan should include only those levels.

#### Task sequence adjustments

- If the scope involves both modifications and new needs, interleave them: modify existing needs first, then create new needs that fill gaps.
- If the user explicitly requests to skip a step, omit it from the plan. In enforcing mode, warn that skipping a mandatory gate may block downstream tasks.
- If `pharaoh.toml` is absent, include all steps as recommendations but mark none as mandatory.

---

### Step 5: Present the plan

Format the plan as a structured document the user can review before execution.

**Plan format:**

```
## Implementation Plan

### Scope
- Change: <description of what is changing>
- Type: <modify|create>
- Target needs: <count>
- Affected needs: <count>
- Affected files: <count>
- Strictness: <advisory|enforcing>

### Tasks

| #  | Task                  | Skill            | Target     | Detail                                    | File                     | Required |
|----|-----------------------|------------------|------------|-------------------------------------------|--------------------------|----------|
| 1  | Analyze impact        | pharaoh:change   | REQ_001    | Trace downstream impact of latency change | docs/requirements.rst    | yes      |
| 2  | Update requirement    | pharaoh:author   | REQ_001    | Change latency from 100ms to 50ms         | docs/requirements.rst    | yes      |
| 3  | Update specification  | pharaoh:author   | SPEC_001   | Update signal timing to match new latency | docs/specifications.rst  | yes      |
| 4  | Update implementation | pharaoh:author   | IMPL_001   | Adjust timer configuration                | docs/implementations.rst | yes      |
| 5  | Update test case      | pharaoh:author   | TC_001     | Update expected timing in assertions      | docs/test_cases.rst      | yes      |
| 6  | Verify all changes    | pharaoh:verify   | (all)      | Verify REQ_001, SPEC_001, IMPL_001, TC_001| --                       | yes*     |
| 7  | MECE check            | pharaoh:mece     | (all)      | Check for gaps in modified area           | --                       | no       |

*Required in enforcing mode when require_verification = true.

### Dependencies
- Task 1 must complete before Tasks 2-5 (change analysis before authoring).
- Tasks 2-5 should execute in order (top-down through hierarchy).
- Task 6 requires Tasks 2-5 to complete (verification after all authoring).
- Task 7 can run after Task 6 or independently.

### Estimated scope
- Needs to modify: <count>
- Needs to create: <count>
- Files to touch: <count>
```

**Presentation rules:**

- Number every task sequentially starting from 1.
- For each task, specify the exact skill to invoke, the target need ID, a concise description of the change, and the source file.
- Mark tasks as "Required" based on workflow gates and strictness mode:
  - In enforcing mode: tasks mandated by workflow gates are marked `yes`.
  - In advisory mode: all tasks are marked `recommended` instead of `yes`. No task is strictly required.
- Show dependencies explicitly so the user understands the execution order.
- If the plan has more than 10 tasks, group them by hierarchy level with subtotals.

---

### Step 6: Offer execution

After presenting the plan, ask the user how they want to proceed:

```
Execute this plan step by step?

Options:
  1. Execute all tasks in sequence
  2. Execute up to task N (partial execution)
  3. Modify the plan first
  4. Save the plan and execute later
```

**If the user chooses to execute:**

1. Begin with Task 1. Invoke the specified skill with the specified target and parameters.
2. After each task completes, report progress:
   ```
   Task 2/7 complete: Updated REQ_001 (latency changed to 50ms).
   Proceeding to Task 3: Update SPEC_001...
   ```
3. If a task fails or produces unexpected results, pause and report:
   ```
   Task 3 encountered an issue: SPEC_001 has additional links to IMPL_002
   that were not in the original scope.

   Options:
     1. Add IMPL_002 to the plan and continue
     2. Skip SPEC_001 and continue with Task 4
     3. Stop execution and revise the plan
   ```
4. Allow the user to pause at any point. If the user says "pause," "stop," or "wait," halt execution immediately and report the current state:
   ```
   Plan paused after Task 3/7.
   Completed: Tasks 1-3
   Remaining: Tasks 4-7

   Resume with "continue" or modify the remaining tasks.
   ```
5. Update `.pharaoh/session.json` as each skill completes, following the state management rules in `skills/shared/strictness.md`. This ensures that workflow gates are satisfied as the plan progresses.

**If the user chooses to modify the plan:**

1. Ask what changes they want: add tasks, remove tasks, reorder tasks, or change task details.
2. Rebuild the plan with the modifications.
3. Re-present the updated plan and offer execution again.

**If the user chooses to save:**

1. Present the plan in a copyable format (the table above).
2. Inform the user they can invoke individual skills manually following the plan order.
3. Note which tasks are required by workflow gates if in enforcing mode.

---

### Step 7: Handle edge cases during execution

**New impacts discovered mid-execution:**

If authoring a need reveals additional downstream impacts not captured in the original Change Document:

1. Pause execution.
2. Report the newly discovered impacts.
3. Offer to extend the plan with additional tasks for the new impacts.
4. Resume only after the user confirms the updated plan.

**Enforcing mode gate failures:**

If a task cannot execute because a prerequisite gate is not satisfied:

1. Report which gate failed and which prerequisite is missing.
2. Check if the missing prerequisite is a task earlier in the plan that was skipped.
3. Offer to insert or re-run the prerequisite task.
4. Do not silently skip the blocked task.

**Conflicting changes:**

If two tasks in the plan modify the same need (e.g., a specification is affected by changes to two different requirements):

1. Detect the conflict when building the plan in Step 4.
2. Merge the two tasks into a single authoring task that addresses both changes.
3. Note the merge in the plan: `Update SPEC_001 (affected by REQ_001 and REQ_003)`.

---

## Strictness Behavior

### Advisory mode

- The plan includes all recommended tasks in the proper order.
- No task is marked as strictly required.
- The user can skip any task during execution.
- After skipping a recommended task, show a tip:
  ```
  Tip: Skipping change analysis. Consider running pharaoh:change later
  to document the impact of these modifications.
  ```
- Do not block execution for any reason.

### Enforcing mode

- Tasks mandated by workflow gates are marked as required in the plan.
- During execution, if the user attempts to skip a required task, block with a clear message:
  ```
  Blocked: Task 1 (change analysis) is required before authoring tasks
  can execute. This is enforced by pharaoh.toml:
    [pharaoh.workflow]
    require_change_analysis = true

  Run the change analysis first, or switch to advisory mode in pharaoh.toml.
  ```
- The plan must include change analysis before any authoring tasks when `require_change_analysis = true`.
- The plan must include verification before any release task when `require_verification = true`.
- The plan must include a MECE check before any release task when `require_mece_on_release = true`.
- If a required task fails, execution halts. The user must resolve the failure before continuing.

---

## Key Constraints

1. **Keep plans concrete.** Every task must specify which need to modify or create, what the change is, and which file is involved. Vague tasks like "update related specs" are not acceptable. Name each need explicitly.

2. **Never auto-execute without user consent.** Always present the plan and wait for explicit confirmation before invoking any skill. This applies even if the plan has only one task.

3. **Allow plan modification before and during execution.** The user can add, remove, reorder, or change tasks at any point. Re-present the modified plan before resuming execution.

4. **Respect the hierarchy.** Author needs top-down: requirements before specifications, specifications before implementations, implementations before test cases. This ensures parent content is finalized before children are updated.

5. **One skill invocation per task.** Each task in the plan maps to exactly one Pharaoh skill call. Do not combine multiple skill invocations into a single task.

6. **Handle partial execution gracefully.** If execution is paused or interrupted, the plan state (which tasks are complete, which remain) must be clear to the user. Completed tasks should already be reflected in `.pharaoh/session.json`.

7. **No session state changes from planning alone.** Building and presenting the plan does not modify `.pharaoh/session.json`. State is only updated when tasks are actually executed.

8. **No workflow gates on this skill.** As noted in `skills/shared/strictness.md`, `pharaoh:plan` has no prerequisites and executes freely in both advisory and enforcing modes.

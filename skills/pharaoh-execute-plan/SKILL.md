---
name: pharaoh-execute-plan
description: Use when executing a plan.yaml produced by pharaoh-write-plan. Reads the plan, runs each task (inline or via subagent dispatch), threads outputs between tasks per the ref grammar, validates outputs via pharaoh-output-validate, persists artefacts and report.yaml. Generic — the plan is the orchestrator, this skill is the engine.
---

# pharaoh-execute-plan

## Invariant: every `completed` task has output on disk

A task marked `status: completed` MUST have its declared output present on disk — an artefact file at the path from Step 4.6 (emission tasks) or a `return.json` at `<workspace_dir>/runs/<task_id>[/<foreach_index>]/return.json` (check / review / gate tasks). Tasks that "completed inlined without output" do not exist. If a task cannot produce its output, mark it `failed` or `skipped` with a reason — never `completed`. Step 4.10 (`output_presence_audit`) enforces this before `report.yaml` is written; missing output rewrites the task status to `reporting_error` and the plan status to `failed` with reason `missing_task_output`. Skipping or collapsing per-foreach-instance `return.json` files into one summary defeats `pharaoh-self-review-coverage-check`, which reads the files directly.

## When to use

Invoke when you already have a plan.yaml and want to execute it. The plan carries everything the executor needs: task graph, skill references, input refs, validation rules, execution-mode defaults. This skill never authors plans (that is `pharaoh-write-plan`) and never reviews results (that is `pharaoh-quality-gate` or a human).

Also: this skill replaces the prose-orchestration of old composition skills like `pharaoh-feats-from-project` and `pharaoh-reqs-from-module`. Those made the LLM execute a 12-step process by reading prose; this skill executes a DAG declared as data. If you find yourself reading a multi-step prose-orchestration skill, stop and look for a plan.yaml instead.

## Atomicity

- (a) **Indivisible.** One plan.yaml in, one report.yaml plus an artefacts directory out. No plan authoring. No review. No domain-specific behaviour. Adding a feature to the executor means extending the schema, not this skill.
- (b) **Typed I/O.**
  - Input: `{plan_path: str, project_root: str, workspace_dir?: str, execution_mode_override?: "inline"|"subagents"}`.
  - Output: `{status: "completed"|"aborted"|"partial", report_path: str, artefacts_dir: str, failed_task_ids: list[str]}`.
- (c) **Execution-based reward.** Fixture in `pharaoh-validation/fixtures/execute-plan-smoke/` contains a 3-task plan using mock-emit skills (each returns a deterministic string given its input). After the executor runs:
  1. `report.yaml` exists and parses.
  2. All three tasks appear under `tasks:` with `status: completed`.
  3. Artefact files exist under the workspace at the paths declared in the report.
  4. Ref resolution worked: task 2 and task 3 received task 1's output verbatim (captured by the mock).
- (d) **Reusable.** Any plan that conforms to `schema.md`. Forward-engineering, reverse-engineering, migration — all look alike to the executor.
- (e) **Composable.** Called by higher-level skills or directly by the user. The only skill it calls internally is `pharaoh-output-validate`; per-task skill dispatch is parameterised by `skill:` in the plan.

## Input

- `plan_path`: absolute path to plan.yaml.
- `project_root`: absolute path. Must match the plan's `project_root` (else fail with `project_root_mismatch`).
- `workspace_dir` (optional): absolute path. If omitted, resolved from plan's `workspace_dir` or default `<project_root>/.pharaoh/runs/<plan.name>-<timestamp>/`.
- `execution_mode_override` (optional): overrides `defaults.execution_mode` in the plan. Individual tasks with their own `execution_mode:` still win over this override.

## Output

A mapping:

```yaml
status: completed | aborted | partial
report_path: <abs_path_to_report.yaml>
artefacts_dir: <abs_path_to_artefacts_dir>
failed_task_ids: [<id>, ...]
```

`status`:
- `completed` — all tasks reached `completed` status.
- `partial` — some tasks `failed` or `skipped` under `on_fail: skip_dependents`; others ran to completion.
- `aborted` — an `on_fail: abort_plan` rule fired, or the plan itself was rejected at static validation.

## Process

### Step 1: Load and validate plan

1. Read `plan_path`. Parse as YAML. On parse error → return `{status: "aborted", ...}` with the parse error recorded in `report.yaml`.
2. Validate against `schema.md`:
   - Required top-level fields present.
   - No unknown top-level fields.
   - `version == 1`.
   - Every task has required fields; no unknowns.
   - Every `skill:` references a directory present under `<pharaoh>/skills/` or `<papyrus>/skills/`.
3. Confirm `project_root` input matches plan's declared `project_root`. Mismatch → abort.
4. Resolve `workspace_dir`. Create directory if missing.

### Step 2: Static ref analysis

Before any task runs, walk every task's `inputs`, `depends_on`, `foreach`:

1. Parse each `${...}` ref. Syntax errors → abort plan; record which task and which field.
2. For each ref, resolve the producing task id. Unknown producer → abort.
3. For each ref using a helper, confirm the helper exists in the helper set declared in `schema.md`. Unknown helper → abort.
4. Build the dependency graph (explicit `depends_on` ∪ implicit deps from refs).
5. Detect cycles via DFS. Any cycle → abort; list the cycle in the report.
6. Validate `parallel_group` invariants: every group's members share the same `depends_on` set, no intra-group deps.
7. Warn (do not abort) on declared `outputs:` refs to fields not enumerated in the producer's `outputs:` map. Documentary only.

Abort here means `status: "aborted"`, zero tasks executed, report written with the specific error.

### Step 3: Topological order

Produce a partial order: list-of-lists where each inner list is a "wave" — tasks with all upstream deps satisfied. Within a wave, tasks sharing a `parallel_group` are candidates for concurrent dispatch in subagents mode.

Foreach-expanded tasks are expanded into concrete instances at this step: if `foreach: ${upstream}` produces N items, emit N logical tasks with ids `<task.id>[0]`, …, `<task.id>[N-1]`. Instance inputs are resolved per-iteration with `${item}` bound.

### Step 3.5: Resolve execution mode (interactive for ambiguous foreach)

Before Step 4 dispatches anything, walk every foreach-expanded task and determine its effective execution mode. Priority (first match wins):

1. Executor was invoked with `execution_mode_override` → use the override. Skip prompting.
2. The task has an explicit `execution_mode:` field → use that value.
3. `plan.defaults.execution_mode` is a concrete mode (`inline`, `subagents`, `family-bundle`) → use the plan default.
4. Plan default is `ask` OR plan default is absent → GATE. Emit the prompt below, collect the user's answer, apply it to every expanded instance of this task.

The gate fires at most once per foreach-originating task, not once per instance. Non-foreach tasks default to `inline` (no prompt); the gate exists specifically to prevent silent scope collapse on large fan-outs.

**Prompt shape.** For each ambiguous foreach task (N instances), emit to the controller:

```
Task `<task_id>` has foreach over `<upstream_ref>` and expanded to <N> instances.
How should the executor dispatch them?

  [inline]              Run instances sequentially in this conversation.
                        Cheapest. No cross-instance atomicity — the controlling
                        agent sees every instance's inputs and outputs. Good for
                        N ≤ 3 and deterministic skills.

  [subagents]           Dispatch one subagent per instance. Full atomicity — each
                        subagent sees only its resolved inputs. Respects per-
                        instance caps (e.g. "5-7 comp_reqs per feat"). Expensive
                        at N > 20.

  [family-bundle]       Group instances by a bundle key and dispatch one subagent
                        per bundle. Middle ground. Per-instance caps are NOT
                        enforced across the bundle — prior dogfooding confirmed
                        sibling instances leak into each other when one subagent
                        sees multiple foreach scopes at once.

Choose one (inline | subagents | family-bundle):
```

If the user picks `family-bundle`, follow up with:

```
bundle_key (ref, e.g. `${item.feat_id}` or `${heuristics.<helper>(item.file)}`):
```

The user's answer is a valid ref per the schema's ref grammar. Validate it syntactically; on malformed ref, re-prompt once; on second failure, fall back to `subagents` mode and warn.

**Recording.** Every gate decision lands in `report.yaml` under the task's entry:

```yaml
tasks:
  <task_id>:
    execution_mode_decision:
      resolved_mode: inline | subagents | family-bundle
      source: override | task_level | plan_default | user_prompt
      bundle_key: <ref>      # only when resolved_mode=family-bundle
      prompted_at: <iso8601> # only when source=user_prompt
```

This makes the decision auditable — if the pilot review says "executor silently bundled", the report either proves or disproves it.

**Non-interactive callers.** When the executor cannot accept a response (e.g. running under a CI harness), treat `ask` as an error: abort the plan with `status: aborted` and note `execution_mode_gate_cannot_prompt`. Callers that want unattended execution must set `defaults.execution_mode` to a concrete mode or pass `execution_mode_override`.

### Step 4: Per-task execution loop

For each wave in order:

4.1. **Dispatch plan.** Per-task resolved execution mode (from Step 3.5) drives dispatch shape:

  - **inline**: the controlling agent executes each instance sequentially in-context. `parallel_group` is informational only.
  - **subagents**: dispatch one subagent per task (or per foreach instance). Group members in the same `parallel_group` dispatch in one turn via parallel Task tool calls.
  - **family-bundle**: evaluate the task's `bundle_key` for every foreach instance. Partition instances by resolved key. Dispatch one subagent per bundle; each subagent receives the family-bundle variant of `implementer-prompt.md` and runs the skill once per item in its bundle. Bundles sharing a `parallel_group` dispatch concurrently.

  Tasks without foreach with `family-bundle` configured are a schema error (caught at Step 2); at this point every family-bundle task is foreach-expanded.

4.2. **Per task, resolve runtime refs.** Look up each input ref in the in-memory artefact store. If any ref is unresolvable (upstream failed/skipped), mark this task `blocked`, apply its `on_fail` policy, continue.

4.3. **Render implementer prompt.** Use `implementer-prompt.md` as the template. Fill variables:
  - `{skill_name}` — from task's `skill:`
  - `{skill_body}` — full contents of `<skills>/<skill_name>/SKILL.md`, minus frontmatter
  - `{task_id}` — e.g. `map_files[3]` for foreach instance 3
  - `{task_inputs_yaml}` — the resolved input map as YAML
  - `{expected_output_schema}` — task's `expected_output_schema` or "unspecified"
  - `{project_root}`, `{workspace}` — absolute paths.

4.4. **Dispatch.**
  - `inline` mode: the controlling agent (the one running this skill) reads the rendered prompt and performs the atomic skill's process directly in-context. Record the output when done.
  - `subagents` mode: invoke the Task tool with the rendered prompt as the subagent's whole brief. Capture the subagent's return message.
  - `family-bundle` mode: render the family-bundle variant of `implementer-prompt.md` (one subagent covers all bundle items). Dispatch via Task tool. Capture the subagent's multi-output return (one artefact per bundle item, in the order the subagent was handed them). Validate each artefact independently per Step 4.5.

4.5. **Validate output.** Run `pharaoh-output-validate` with:
  - `output_text` = dispatched task's return value
  - `target_schema` = `expected_output_schema` if set, else any `validation` rule targeting this task, else skip validation.
  - `schema_context` = `{directive: ..., required_options: [...]}` when the schema is `rst_directive`; empty for other schemas.
  - `strip_fences: true`

4.6. **Handle validation result.**
  - `valid: true` → persist the parsed/stripped artefact to `<workspace>/artefacts/<task_id>.<ext>` where `.ext` is `.rst` for directives, `.yaml` for yaml, `.txt` default. Mark task `completed`. Update in-memory artefact store with the task's output.
  - `valid: false` and retries remaining → increment retry counter, rebuild prompt with stricter preamble (see below), re-dispatch.
  - `valid: false` and retries exhausted → apply the validation rule's `on_fail` policy.

4.7. **Retry preamble.** When re-dispatching after a validation failure, prepend to the prompt:

```
STRICT OUTPUT REQUIRED. Your previous attempt failed validation with:
<errors joined with ';'>
Emit ONLY the artefact content expected by the target schema. No prose wrapper. No markdown fences. No typos in option keys.
```

4.8. **On_fail policies.**
  - `retry` — already consumed; after exhaustion treat as `skip_dependents`.
  - `skip_dependents` — mark this task `failed`. Mark every transitive dependent `skipped`. Continue with independent branches of the DAG. Final plan status becomes `partial`.
  - `abort_plan` — mark this task `failed`. Stop dispatching. Emit report. Status `aborted`.

4.9. **Parallel dispatch.** In subagents mode within a parallel_group, dispatch all tasks in the group in one message (multiple Task tool calls in one turn). Wait for all to return before moving to the next wave. Per-task validation and retry still happen; retry re-dispatches only the failing task, not the whole group.

4.10. **`output_presence_audit` — run before Step 5.** For every task whose in-memory status is `completed`, verify that its declared output exists on disk AND is non-empty:

  - **Emission tasks** (skill emits RST directives, YAML, diagrams, etc.): the task's artefact file persisted in Step 4.6 (`<workspace>/artefacts/<task_id>.<ext>`, or `<...>/artefacts/<task_id>/<foreach_index>.<ext>` for foreach). File must exist and `size > 0`.
  - **Check / review / gate tasks** (skill emits JSON findings — `pharaoh-req-review`, `pharaoh-req-code-grounding-check`, `pharaoh-diagram-review`, `pharaoh-feat-review`, `pharaoh-diagram-lint`, `pharaoh-quality-gate`, `pharaoh-output-validate`, `pharaoh-self-review-coverage-check`, any future atom-check role): a `return.json` under `<workspace>/runs/<task_id>[/<foreach_index>]/return.json`. File must exist, parse as JSON, and be a non-empty object. For foreach tasks, verify one `return.json` per foreach instance (count ≥ instance count from the expansion in Step 4.1).
  - **Composition / plumbing tasks** (skill emits only in-memory data used by downstream refs — `pharaoh-id-allocate`, `pharaoh-feat-file-map`, `pharaoh-context-gather`): require a `return.json` at `<workspace>/runs/<task_id>/return.json` capturing the in-memory output that downstream refs resolved.

  For each task that fails this audit:
  1. Rewrite its report status from `completed` to `reporting_error`.
  2. Append a `reporting_errors` entry naming the missing path.
  3. Mark the plan's overall status as `failed` with reason `missing_task_output` (overrides a previously-clean status; does NOT override `aborted`).

  The audit is mandatory. Skipping or collapsing it is the exact failure mode called out in the invariant at the top of this skill.

### Step 5: Emit report

After the loop terminates (completion, partial, or abort):

1. Write `report.yaml` to `<workspace_dir>/report.yaml` per the schema in `schema.md#report-yaml`.
2. Include every task (completed, failed, skipped, blocked, `reporting_error`).
3. Include foreach instances under `foreach_instances:` for tasks that had foreach.
4. Include top-level `reporting_errors:` list if Step 4.10's audit caught anything; each entry is `{task_id, foreach_index?, expected_path, reason: "missing" | "empty" | "unparseable"}`.
5. Return `{status, report_path, artefacts_dir, failed_task_ids, reporting_errors}`.

## Failure modes

| Condition                                  | Response                                                       |
| ------------------------------------------ | -------------------------------------------------------------- |
| Plan YAML invalid                          | status=aborted; report notes `plan_invalid: <parse_error>`.    |
| Schema violation                           | status=aborted; report notes which rule failed.                |
| project_root mismatch                      | status=aborted.                                                |
| Unknown skill                              | status=aborted at static validation.                           |
| Cyclic dep                                 | status=aborted; cycle printed.                                 |
| Unresolvable ref at runtime                | task=blocked; on_fail policy applies.                          |
| pharaoh-output-validate errors internally  | Log, treat as validation failure (conservative).               |
| Task dispatch returns empty                | Treat as validation failure with error `empty_output`.         |
| Subagent Task tool fails                   | Retry once; on second failure mark task failed.                |
| `completed` task has no output on disk     | Step 4.10 rewrites to `reporting_error`; plan status=`failed`. |

## Worked example

Plan (excerpt):

```yaml
name: smoke
version: 1
project_root: /tmp/fixture
tasks:
  - id: feats
    skill: pharaoh-feat-draft-from-docs
    inputs:
      docs_root: docs
    outputs:
      feats: list
    expected_output_schema: rst_directive
  - id: map
    skill: pharaoh-feat-file-map
    foreach: ${feats.feats}
    inputs:
      feat_id: ${item.id}
      feat_title: ${item.title}
      feat_body: ${item.body}
      src_root: src
    depends_on: [feats]
    parallel_group: map_files
```

Execution trace (2 feats discovered):

1. Wave 1: `feats` runs inline. Returns 2 directive blocks. Validated as rst_directive. Parsed `feats:` list cached to store.
2. Wave 2: `map` expands to `map[0]`, `map[1]`. Both share parallel_group `map_files`. In subagents mode: dispatched together in one turn. Each returns YAML; validated against yaml schema; persisted.
3. Report lists `feats: completed` and `map: completed` with `foreach_instances: [index:0 completed, index:1 completed]`.

## Non-goals

- Does not author plans.
- Does not choose `execution_mode` based on heuristics — that is the plan's business (via `defaults` or per-task override).
- Does not perform cross-plan dedup or impact analysis — those are separate skills.
- Does not log progress to stdout beyond the final return value; structured progress lives in report.yaml.

## Relationship to deleted composition skills

`pharaoh-feats-from-project` and `pharaoh-reqs-from-module` previously encoded orchestration in prose. They have been deleted in favour of this skill + `pharaoh-write-plan`. The domain heuristics those skills carried (split_strategy selection, preseed-before-reqs ordering, quality-gate wiring, id-allocate positioning) moved to `pharaoh-write-plan`'s plan-authoring logic. The executor itself is domain-free.

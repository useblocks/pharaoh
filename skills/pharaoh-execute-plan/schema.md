# plan.yaml schema

This file specifies the plan.yaml contract between `pharaoh-write-plan` (producer) and `pharaoh-execute-plan` (consumer). Any other skill or human authoring a plan must conform to this schema. The executor rejects plans that violate it.

Version: 1.

## Top-level fields

```yaml
name: <string>                    # required. descriptive plan name, used in report and logs.
version: <int>                    # required. currently the only supported value is 1.
project_root: <abs_path>          # required. absolute path; all relative paths in inputs resolve against this.
workspace_dir: <abs_path>         # optional. where the executor writes artefacts + report.yaml. default: <project_root>/.pharaoh/runs/<name>-<timestamp>/.
defaults:                         # optional. per-task defaults; each task may override.
  execution_mode: <mode>          # "inline" | "subagents" | "family-bundle" | "ask". default "ask".
  retry_on_validation_fail: <int> # default 1. applies per task; 0 disables retry.
tasks:                            # required. list of task objects, order-insignificant (DAG).
  - <task>
validation:                       # optional. list of post-hoc validation rules.
  - <validation_rule>
```

All field names are lowercase snake_case. Unknown top-level fields are rejected.

## Task object

```yaml
- id: <slug>                      # required. unique within plan. matches `^[a-z][a-z0-9_]*$`.
  skill: <skill_name>             # required. name of an atomic skill in pharaoh/skills/ or papyrus/skills/.
  inputs:                         # required. map of skill-input-name → value or ref.
    <key>: <value_or_ref>
  depends_on: [<task_id>, ...]    # optional. explicit dependencies. implicit deps via ${ref} are always added.
  foreach: <ref>                  # optional. expands this task to N instances, one per item in the referenced list.
  parallel_group: <slug>          # optional. tasks sharing a group execute concurrently when execution_mode=subagents.
  execution_mode: <mode>          # optional. overrides defaults.execution_mode for this task. "inline" | "subagents" | "family-bundle" | "ask".
  bundle_key: <ref>               # required iff execution_mode == "family-bundle". ref-grammar expression evaluated per foreach instance; instances sharing the same evaluated key dispatch in one subagent. See Execution modes below.
  retry_on_validation_fail: <int> # optional. overrides defaults.retry_on_validation_fail.
  expected_output_schema: <name>  # optional. named schema from pharaoh-output-validate (e.g. "rst_directive"). hint for executor; does NOT replace the validation block.
  outputs:                        # optional. declares fields the task is expected to produce. purely documentary; executor does not enforce.
    <key>: <type_hint>
```

Unknown task-level fields are rejected. Either `inputs` is empty dict or a non-empty map; missing `inputs` is rejected (explicit is better than implicit).

## Ref resolution (`${...}`)

A string value that matches `^\$\{[^}]+\}$` is a reference. A value may ONLY be wholly a ref (no interpolation inside larger strings). Supported forms:

| Form                              | Meaning                                                                                           |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| `${task_id}`                      | Shorthand for `${task_id.output}` — the task's single-output default.                             |
| `${task_id.field}`                | Field from a task's output mapping.                                                               |
| `${task_id.field.subfield}`       | Nested field access. Max depth 4. Executor rejects deeper refs.                                   |
| `${item}`                         | Only valid inside a `foreach`-expanded task. Current iteration's item.                            |
| `${item.field}`                   | Field of the current foreach item when the iterated value is a mapping.                           |
| `${workspace}`                    | Resolves to `workspace_dir`.                                                                      |
| `${project_root}`                 | Resolves to top-level `project_root`.                                                             |
| `${heuristics.<name>(<arg>)}`     | Pure helper function. `<arg>` is either a bare dotted ref path (e.g. `item.file`) or a double-quoted string literal (e.g. `"src/foo.py"`). Single argument only. No `${}` inside the parens. |
| `${task_id.field \| helper}`      | Pipe a value through a helper (filter-style). Same helper set as above. Helper arguments use parens: `\| by_stem(item.stem)` or `\| by_stem("foo")`. |

No other ref forms are permitted. Arithmetic, string concatenation, env-var lookups, shell interpolation — all rejected. If a consumer needs richer composition, add a dedicated helper.

### Static ref validation

Before any task runs, the executor walks every task's `inputs`, `depends_on`, and `foreach` fields and:

1. Parses every ref syntactically. Syntax errors fail the plan.
2. Resolves the producing task. Missing producers fail the plan.
3. Checks the producing task's declared `outputs` map (if present) for the referenced field. Unknown fields are WARNINGs when `outputs` is present, not failures — the declaration is documentary.
4. Builds a DAG from `depends_on` plus implicit deps from refs. Detects cycles; cycles fail the plan.

Static validation runs fast (no skill dispatch) so ref bugs fail before a single LLM call.

### Runtime ref resolution

At dispatch time for task T:

1. For each ref in T's inputs, look up the producing task's actual output from the in-memory artefact store.
2. If the producing task is a foreach-expanded task, the ref resolves to a list of all iterations' outputs (order matches foreach input order).
3. Apply helper if piped.
4. Substitute into input map.
5. If any ref is unresolvable at runtime (e.g., upstream task failed and executor still attempted dispatch due to a race), the task fails with `status=BLOCKED` and the error `unresolved_ref: <ref>`.

## Foreach

```yaml
- id: map_files
  skill: pharaoh-feat-file-map
  foreach: ${draft_feats.feats}
  inputs:
    feat_id: ${item.id}
    feat_title: ${item.title}
```

Semantics:
- `foreach` takes exactly one ref whose resolved value must be a list.
- Executor instantiates one logical task per item, with `${item}` bound to that item.
- Each instance gets a concrete id formed as `<task.id>[<index>]` (0-indexed). That ID is the key in the artefact store.
- When a downstream task references `${map_files.files}` (no index), it receives a list of all instances' `files` fields, order preserved.
- When a downstream task has its own `foreach: ${map_files}`, the downstream receives the list-of-outputs directly and iterates.
- A `parallel_group` on a foreach task applies to every instance: all N instances share the group and run concurrently.
- Foreach over an empty list produces zero instances. Downstream refs resolve to empty lists. This is not a failure.

Nested foreach (foreach depending on a foreach's output) is permitted only when the downstream expands the flat list of upstream outputs, not when it tries to expand per-upstream-item. Exactly:

```yaml
# OK: flat expansion over all feats × files.
- id: reqs
  foreach: ${map_files.files_flat}   # flat list of {feat_id, file} pairs.
  inputs:
    file_path: ${item.file}

# NOT OK: forbidden — executor rejects at static validation.
- id: reqs_per_feat
  foreach: ${map_files}  # list of lists — would need 2-level iteration
  inputs:
    ...
```

The producer is expected to emit a flat list (e.g., `files_flat`) for cross-product iteration. This keeps executor logic simple.

## Helpers

Executor ships with a closed set of pure helpers. No user-defined functions; no sandbox. Adding a helper is a schema-version bump.

| Helper                                          | Purpose                                                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `${heuristics.split_strategy(<file_path_ref>)}` | Returns `"single" \| "sections" \| "top_level_symbols"` per the heuristic (LOC + marker regex).        |
| `${list \| flatten}`                            | `[[a,b],[c]] → [a,b,c]`. For foreach-output lists whose items are themselves lists.                    |
| `${list \| to_papyrus_seeds}`                   | Maps a list of feat-directive objects to the seeds format `pharaoh-decision-record` expects. Each seed is `{canonical_name: <feat_id>, body: <feat_title + " is the canonical feat id">}`. |
| `${list \| to_files_flat}`                      | Denormalises a list of feat-file-map outputs (each a flat mapping `{feat_id, files, rationale, entry_point?, shared_with?}`) into a flat list `[{file: <path>, feat_id: <id>, stem: <basename_no_ext>, parents: [<feat_ids>]}, ...]`. Files appearing under multiple feats (across foreach instances) are emitted once with a populated `parents` list. |
| `${list \| to_id_requests}`                     | Converts a flat file list (output of `to_files_flat`) to `pharaoh-id-allocate` request shape `[{stem, count: 3, prefix, type, parent_feat_id: parents[0]}, ...]`. Takes default count=3 per file; prefix inferred from the plan's declared type. |
| `${mapping \| by_stem(<stem_ref>)}`             | Given an id-allocate output mapping `{stem: [id1, id2, ...], ...}` and a stem, returns the list of ids for that stem. Used to thread allocated ids into per-file req tasks.                             |
| `${list \| with_entry_point}`                   | Filters a list of feat-file-map outputs to only those having an `entry_point` field set.               |
| `${list \| unique}`                             | Dedup preserving first occurrence.                                                                     |
| `${mapping \| keys}`                            | Emits the keys of a mapping as a list.                                                                 |

Any ref using an unknown helper fails static validation.

## Parallel group

Tasks tagged with `parallel_group: <slug>` execute concurrently in `subagents` mode. In `inline` mode, `parallel_group` is informational (noted in report.yaml, but tasks still run sequentially). Membership rules:

- All tasks in a group must share the same `depends_on` set (dependency-consistent).
- A group may not contain a task that depends on another task in the same group (no intra-group deps). Executor rejects at static validation.
- Groups are unordered relative to each other except via `depends_on`.

## Execution modes

Four modes are supported. The mode determines how a task (or the N instances of a foreach task) are dispatched:

| Mode               | Semantics                                                                                                                                                                                                                                                         | Atomicity                                                                                                                      | Typical cost                                        |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| `inline`           | The controlling agent (the one running `pharaoh-execute-plan`) performs the skill in-context, task by task, sequentially. For foreach tasks, all N instances run in the same context.                                                                             | No cross-instance isolation. The same agent sees every instance's inputs and outputs; per-instance caps are self-enforced only. | Cheapest. One conversation.                         |
| `subagents`        | Same as `subagents-per-task` — one subagent dispatched per task. For foreach tasks, N instances → N subagents. Group members in a `parallel_group` dispatch in one turn when possible.                                                                             | Full per-instance atomicity. Each subagent sees only its resolved inputs.                                                      | Most expensive. N dispatches.                        |
| `family-bundle`    | Requires `bundle_key`. For foreach tasks, the executor evaluates `bundle_key` per instance, groups instances by the resolved key, and dispatches one subagent per bundle. The subagent runs the skill once per item in its bundle, in order.                        | Per-bundle atomicity only. Within a bundle, the subagent sees all items' inputs; per-instance caps are NOT enforced across the bundle. | Middle ground. M subagents where M = unique keys.    |
| `ask`              | The executor stops at the first wave that contains ambiguous foreach tasks (no task-level `execution_mode`, no plan-level concrete default) and prompts the user to choose one of the concrete modes above. Selection is recorded in `report.yaml`. See `pharaoh-execute-plan/SKILL.md` Step 3.5 for the exact prompt text and response handling. | Depends on the chosen mode.                                                                                                     | Depends on the chosen mode.                         |

When `defaults.execution_mode` is absent, the default is `"ask"` — the executor WILL pause for user input on the first ambiguous foreach. Plan authors who want unattended execution set `defaults.execution_mode` to a concrete mode (e.g. `"subagents"`), or set `execution_mode:` per-task.

`bundle_key` rules:

- Only meaningful when `execution_mode: family-bundle`. Rejected (schema error) on any other mode.
- Accepts the ref grammar used elsewhere. Typical: `${item.feat_id}`, `${item.family}`, `${heuristics.<helper>(item.file)}`.
- Evaluated per foreach instance at dispatch time. Result must be a string or scalar; lists/mappings are rejected.
- Instances whose key evaluates to the same value are dispatched as one bundle, up to one subagent per bundle.
- Single-instance bundles behave identically to `subagents` mode for that bundle.
- Foreach-expanded task in `family-bundle` mode with `parallel_group` set: the group semantics apply across bundles (bundles within the group dispatch concurrently), not within a bundle.

## Validation block

```yaml
validation:
  - task_output: <ref>
    schema: <schema_name>         # name from pharaoh-output-validate.
    on_fail: <policy>             # "retry" (default) | "skip_dependents" | "abort_plan"
  - task_output: ${reqs.*}        # wildcard expands to every foreach instance's output.
    schema: rst_directive
```

- Executor runs these rules after each task completes.
- `on_fail: retry` — re-dispatch the task with the validator's error appended to the prompt, up to `retry_on_validation_fail` times.
- `on_fail: skip_dependents` — record failure, mark the task's transitive dependents as SKIPPED, continue with other branches of the DAG.
- `on_fail: abort_plan` — record failure, halt the executor, emit report.yaml with `status: aborted`.

If no validation rule targets a task's output, only the task's own `expected_output_schema` hint is applied (with default `on_fail: retry`).

## Failure modes (plan-level)

| Condition                                                       | Executor behaviour                           |
| --------------------------------------------------------------- | -------------------------------------------- |
| YAML parse error                                                | Reject plan. No tasks run.                   |
| Unknown top-level field                                         | Reject plan.                                 |
| Task id duplicate                                               | Reject plan.                                 |
| Unknown skill (not in pharaoh/ or papyrus/ skills dir)          | Reject plan.                                 |
| Cyclic dependency                                               | Reject plan.                                 |
| Unresolvable ref at static validation                           | Reject plan.                                 |
| foreach over a ref whose value at runtime is not a list         | Fail that task as BLOCKED; on_fail policy applies. |
| Static validation warnings (documentary outputs mismatch)       | Log, continue.                               |

## Report.yaml (executor output)

```yaml
plan_name: <name>
plan_version: 1
started_at: <iso8601>
finished_at: <iso8601>
status: completed | aborted | partial
tasks:
  <task_id>:
    status: completed | failed | skipped | blocked
    started_at: <iso8601>
    finished_at: <iso8601>
    execution_mode: inline | subagents
    retries: <int>
    validation:
      - schema: <name>
        result: pass | fail
        errors: [<str>, ...]
    artefact_path: <rel_path_under_workspace>   # relative to workspace_dir
    foreach_instances:                           # present only for foreach tasks
      - index: 0
        status: completed
        artefact_path: ...
```

The report is the single authoritative record of a plan run. No other file format is persisted by the executor.

## Versioning

The schema version is currently 1. Breaking changes (removing fields, changing ref grammar, changing helper signatures) require bumping `version: 2` and supporting both in the executor for one transition period. Additive changes (new helpers, new optional task fields) keep `version: 1`.

## Non-goals

- No loops other than `foreach` (no `while`, no fixed-count `repeat`).
- No conditionals (`if`/`when`). Branch by emitting different task lists at plan-writing time.
- No dynamic re-planning inside the executor. If discovery should reshape the plan, the controlling agent re-invokes `pharaoh-write-plan` with enriched inputs.
- No shell-outs, file I/O, or env reads from ref syntax. Any data the plan needs must arrive via `project_root`, `workspace_dir`, or another task's output.

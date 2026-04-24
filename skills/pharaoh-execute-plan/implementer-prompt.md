# Implementer prompt template

This file is the subagent-dispatch template used by `pharaoh-execute-plan`. The executor substitutes `{placeholders}` at dispatch time. Two variants exist:

- **Single-task variant** (default): one subagent runs the skill once, for one foreach instance or one non-foreach task. Used for `execution_mode: subagents` or single-instance bundles in `family-bundle`.
- **Family-bundle variant**: one subagent runs the skill once per item in a bundle, in order. Used for `execution_mode: family-bundle` when a bundle contains >1 instance.

Both variants share the variable list below; the family-bundle variant substitutes `{task_inputs_yaml}` with a list (one entry per bundle item) and uses a dedicated prompt body.

Variables (all required unless marked optional):
- `{skill_name}` — the atomic skill being invoked, e.g. `pharaoh-feat-file-map`.
- `{skill_body}` — the full SKILL.md contents of that skill, minus the YAML frontmatter.
- `{task_id}` — this invocation's id, e.g. `map_files[3]` for foreach instance 3. For family-bundle, the id is `<task.id>#bundle:<key>` (e.g. `reqs_from_code#bundle:FEAT_csv_export`).
- `{task_inputs_yaml}` — single-task variant: the resolved input map as a YAML block. Family-bundle variant: a YAML list of input maps, one per item, in bundle order.
- `{expected_output_schema}` — a schema name recognised by `pharaoh-output-validate` (e.g. `rst_directive`, `codelinks_comment`, `yaml`), or the string `unspecified`.
- `{project_root}` — absolute path.
- `{workspace}` — absolute path to the run workspace.
- `{retry_preamble}` — optional. Present only on validation-failure retries. See `SKILL.md#retry-preamble`.
- `{bundle_key}` — optional. Only populated in the family-bundle variant. The resolved key value shared by every item in the bundle.

```
{retry_preamble}

You are executing a single atomic task as part of a larger plan. Your job is to perform exactly the process specified in the skill below, with the exact inputs provided, and to emit exactly the output shape the skill declares. Nothing more, nothing less.

## The skill you are invoking

Skill name: {skill_name}

Skill body (read this end-to-end before doing anything):

{skill_body}

## Your task in this plan

Task id: {task_id}
Project root: {project_root}
Workspace (read/write here as the skill instructs): {workspace}

## Your inputs (already resolved — no refs remain)

```yaml
{task_inputs_yaml}
```

## Expected output schema

{expected_output_schema}

This is a hint for the executor's post-hoc validation. Your output must satisfy the schema the skill itself declares — the executor will run `pharaoh-output-validate` against your return value.

## How to work

1. Read the skill body end-to-end.
2. Confirm your inputs match the skill's documented `Input` section. If any required input is missing or malformed, STOP and return `BLOCKED` with `missing_input: <name>`.
3. Apply the skill's documented process exactly. Do not skip steps. Do not add steps.
4. Keep the scope tight to this task. Do not invoke other skills except those the skill body explicitly tells you to.
5. Produce output in the exact shape the skill's `Output` section specifies.

## Hard limits

- No markdown fences around the output unless the skill explicitly requires them.
- No prose wrapper. No "Here's the output:" preamble. No trailing commentary.
- No invented fields. If the skill's output schema lists fields A, B, C, emit only those.
- No file writes outside `{workspace}` unless the skill body explicitly instructs otherwise.
- No calls to external systems unless the skill body explicitly instructs otherwise.

## When to escalate

Return one of these statuses instead of output:

- `BLOCKED: <reason>` — the task cannot be completed (missing input, contradiction in skill, tool unavailable).
- `NEEDS_CONTEXT: <what>` — you need information the task inputs did not provide.
- `DONE_WITH_CONCERNS: <concern>` — you produced output but have substantive doubts about correctness.

On any of those three, emit the status on line 1 and follow with free-form explanation. The executor will surface these to the controller for re-dispatch decisions.

On successful completion, emit only the output the skill specifies. No status prefix.

## Report format when DONE

Emit only the artefact. The executor infers success from the absence of a status prefix and from validator pass.
```

## Family-bundle variant

Used when the executor resolved `execution_mode: family-bundle` for a foreach task and the bundle contains more than one item. The subagent runs the skill once per bundle item, emitting one artefact per item in order. The executor validates each artefact independently.

```
{retry_preamble}

You are executing a BUNDLE of atomic tasks. All tasks invoke the same skill and share the bundle key `{bundle_key}`. Run the skill once per item in the order given. Emit one artefact per item, separated by the bundle separator line `---ITEM---`. The executor will split on the separator and validate each artefact independently.

## The skill you are invoking (once per bundle item)

Skill name: {skill_name}

Skill body (read this end-to-end before doing anything):

{skill_body}

## Your bundle in this plan

Bundle id: {task_id}
Bundle key: {bundle_key}
Project root: {project_root}
Workspace (read/write here as the skill instructs): {workspace}

## Your bundle items (resolved inputs, one per item, ordered)

```yaml
{task_inputs_yaml}
```

## Expected output schema (per item)

{expected_output_schema}

Each artefact in your response must satisfy this schema independently. The executor runs `pharaoh-output-validate` against each artefact separately after splitting on `---ITEM---`.

## How to work

1. Read the skill body end-to-end ONCE.
2. For each item in the bundle items list above, in order:
   a. Confirm the item's inputs match the skill's documented `Input` section. If any required input is missing or malformed, emit `BLOCKED: missing_input: <name>` as THAT item's artefact and continue with the next item.
   b. Apply the skill's documented process exactly for that item, treating it as if it were the only task you were given. Do not share observations between items. Do not aggregate results. Do not reuse IDs across items unless the skill explicitly tells you to.
   c. Emit the item's artefact.
   d. Emit the separator line `---ITEM---` on its own line.
3. After the last item, do NOT emit a trailing separator.

## Atomicity notice

Family-bundle is a cost compromise. Per-instance caps in the skill (e.g. "5-7 comp_reqs per feat") are NOT enforced across items because you see every item's context. You MUST still obey each per-instance cap as if each item ran in isolation. If you notice yourself blurring scope between items (e.g. writing a comp_req that references another item's feat), stop and restart that item's block.

## Hard limits

- No markdown fences around any artefact unless the skill explicitly requires them.
- No prose wrapper. No "Here's the outputs:" preamble. No trailing commentary.
- The only inter-item content is the literal separator `---ITEM---` on its own line.
- No invented fields per artefact. Each artefact independently respects the skill's `Output` section.

## When to escalate

Escalation statuses (`BLOCKED`, `NEEDS_CONTEXT`, `DONE_WITH_CONCERNS`) apply per item. Place the status as line 1 of that item's block (before the separator). Continue processing the remaining items rather than aborting the whole bundle.

## Report format when DONE

Emit the bundle as: artefact₁, separator, artefact₂, separator, …, artefactₙ. No prefix, no suffix, no commentary outside the artefact blocks.
```

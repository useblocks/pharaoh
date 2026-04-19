---
name: pharaoh-review-completeness
description: Atomic — inspect one or more needs for review/approval-chain completeness. Flags needs missing required :reviewer: or :approved_by: fields per the project's artefact catalog. Emits one finding per incomplete need via pharaoh-finding-record.
---

# pharaoh-review-completeness

## When to use

Invoke during audit workflows to check that every need with a required review/approval chain has the corresponding fields populated. Works at single-need granularity (inspect one ID) or over the whole graph (iterate all needs of relevant types).

Do NOT invoke for artefact types whose project tailoring does NOT list `:reviewer:` / `:approved_by:` as required — the skill is a no-op in that case.

## Atomicity

- (a) Indivisible — one lookup + one field-presence check per need.
- (b) Input: `{project_dir, need_ids?: list[str]}` (if `need_ids` omitted, iterate all). Output: `[{need_id, missing_roles: [str]}]` (empty list if all complete).
- (c) Reward: deterministic — field-present vs field-absent. 100% target on fixture.
- (d) Reusable: audit orchestrators, standalone CI gate, pre-merge check.
- (e) Composable: read-only over needs.json + artefact-catalog.yaml.

## Process

### Step 1: Load artefact catalog

Read `<project_dir>/.pharaoh/project/artefact-catalog.yaml` (or `examples/score/.pharaoh/project/artefact-catalog.yaml` if testing against Score). For each artefact type, extract `required_roles` — which may include `reviewer`, `approved_by`, or be absent (no review required).

### Step 2: Load needs

Read `<project_dir>/needs.json` (or the pre-built bazel artefact). For each need matching `need_ids` (or all needs if none given), determine its artefact type from its ID prefix.

### Step 3: Check required roles

For each need whose type has `required_roles`, verify each required role field is present in the need's options and non-empty. Collect missing roles.

### Step 4: Emit findings

For each need with at least one missing role, emit a finding record:

```json
{
  "need_id": "<id>",
  "missing_roles": ["reviewer", "approved_by"]
}
```

Output is a JSON list of such objects, wrapped in a single fenced `json` block. Empty list → `[]`.

No surrounding prose.

## Input / output example

Input call (as audit subagent):
```
pharaoh-review-completeness on project <Score dir> for all component-level reqs
```

Output:
```json
[
  {"need_id": "gd_req__timestamp_recording", "missing_roles": ["approved_by"]}
]
```

## Failure modes

- `artefact-catalog.yaml` absent → emit `[]` with stderr warning; skill is a no-op without tailoring.
- `needs.json` absent → emit `[]` with stderr warning.
- Malformed artefact catalog → emit `[]` with stderr warning `"artefact-catalog malformed"`.

## Composition

Consumed by `pharaoh-audit-fanout` as sub-area 4. Each returned finding is passed to `pharaoh-finding-record` with `category: missing_reviewer` or `category: missing_approval`.

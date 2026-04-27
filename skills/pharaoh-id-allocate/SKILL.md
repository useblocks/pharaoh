---
name: pharaoh-id-allocate
description: Use when about to dispatch a fan-out of emission subagents (pharaoh-req-from-code, pharaoh-feat-draft-from-docs) and you need to pre-allocate globally-unique sphinx-needs IDs. Each subagent receives its pre-allocated pool and emits only from that pool, so parallel agents cannot collide on stem choice. Does NOT invoke emitters, does NOT write RST.
---

# pharaoh-id-allocate

## When to use

Invoke from a plan emitted by `pharaoh-write-plan` (executed via `pharaoh-execute-plan`) before any task that fans out req-emission. Produces a deterministic mapping from `(parent_feat_id, stem)` to a unique list of IDs, so each req-emission task gets its own pre-reserved slots. Without this step, parallel req-emitters choose stems independently and may emit colliding IDs.

Do NOT use to rename existing IDs. Do NOT use to emit reqs. Do NOT use to delete IDs.

## Atomicity

- (a) Indivisible — one request set in → one list of unique IDs out. No subagent dispatch. No file writes. No mutation of the source of `existing_ids`.
- (b) Input: `{existing_ids_file?: str, existing_ids?: list[str], requests: list[{parent_feat_id: str, stem: str, count: int, type: str, prefix: str}]}`. Output: list of allocated ID strings, one per requested slot, in request order. Globally unique across `existing_ids` AND within the returned list.
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-id-allocate/input_spec.json` with 27 planned IDs across 3 features. When `existing_ids` contains `CREQ_writer_01`, the allocator's output for the first `writer` request starts at `CREQ_writer_02`. Output list length equals sum of `requests[].count`.
- (d) Reusable: any fan-out workflow where subagents emit IDs; CI allocators; renumbering utilities.
- (e) Composable: purely pure function. No side effects. No cross-skill calls.

## Input

- `existing_ids_file` (optional): path to a `needs.json` file. The allocator reads every need's `id` field into the existing-id set. If not provided, falls back to `existing_ids`.
- `existing_ids` (optional): explicit list of IDs to treat as already-allocated. Used when no `needs.json` is available.
- `requests`: list of allocation requests. Each request has:
  - `parent_feat_id`: the parent feature this batch belongs to. Used for log messages only; IDs do not include it.
  - `stem`: the per-file / per-symbol disambiguator (e.g. `writer`, `cli`, `exporter`). Usually the file stem normalized to snake_case.
  - `count`: how many IDs to allocate in this batch.
  - `type`: the sphinx-needs directive name (e.g. `comp_req`, `feat`) — recorded in log, not used for ID generation.
  - `prefix`: the ID prefix (e.g. `CREQ_`, `FEAT_`). Determines the allocated ID format.

At least one of `existing_ids_file` or `existing_ids` MUST be provided. Pass `existing_ids=[]` to signal a greenfield project.

## Output

A JSON array of ID strings, in request order. For `requests = [{stem: "a", count: 2, prefix: "CREQ_"}, {stem: "b", count: 1, prefix: "CREQ_"}]`, the output is exactly:

```json
["CREQ_a_01", "CREQ_a_02", "CREQ_b_01"]
```

(assuming no collisions with existing IDs). Callers parse with `json.loads` — no line-oriented or comma-separated alternative.

On any collision, the allocator advances an independent per-stem sequence counter until a free slot is found, then emits exactly `count` IDs per request. If the per-stem counter reaches 99 without emitting `count` free slots, FAIL — excessive collision means the caller chose a poor stem (too generic, reused across many features). The cap aligns with the 2-digit `_<seq:02d>` format: emitted `seq` values stay in `01..99`, never wider.

## Process

### Step 1: Collect existing IDs

If `existing_ids_file` is provided, read it, parse as JSON, extract every `needs[*].id` value into an existing-id set. If `existing_ids` is provided, union its contents into the set. If both are missing, FAIL (caller error).

### Step 2: Allocate per request

Maintain an "allocated in this call" set alongside `existing_ids`. For each request, keep a per-stem `seq` counter (starts at 1). Produce exactly `request.count` IDs by looping `slots_emitted` from 0 to `count - 1`:

1. Generate candidate `<prefix><stem>_<seq:02d>` (e.g. `CREQ_writer_01`).
2. If candidate collides with either set, increment `seq` and retry — the slot is not consumed. If `seq` exceeds 99 without emitting `count` free IDs for this request, FAIL naming the stem and the collision rate.
3. On a non-colliding candidate: add to the "allocated in this call" set, append to the output list, increment `seq`, increment `slots_emitted`.

Exactly `count` IDs per request end up in the output. The per-stem `seq` counter is independent of `slots_emitted` — `seq` only advances on collision; `slots_emitted` only advances on successful emit.

### Step 3: Return

Emit the output as a JSON array of strings (per the wire format declared above). Nothing else on stdout.

## Failure modes

- Neither `existing_ids_file` nor `existing_ids` provided → FAIL.
- `existing_ids_file` path unreadable → FAIL.
- Counter exceeds 99 for any request → FAIL naming the stem.
- Any request has `count < 1` → FAIL.

## Non-goals

- No ID minting strategy beyond sequential numbering — if a project wants UUID-based IDs, this skill is not the right fit.
- No bulk renumbering of existing IDs — this skill only allocates new ones.
- No cross-project uniqueness — scoped to the one project whose `needs.json` (or `existing_ids`) was provided.

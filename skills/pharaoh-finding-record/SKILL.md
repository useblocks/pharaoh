---
name: pharaoh-finding-record
description: Atomic — record an audit finding in the shared Papyrus workspace with automatic dedup. Uses deterministic ID to ensure the same {category, subject_id} tuple never appears twice across concurrent subagents. Returns {action: wrote|duplicate, papyrus_id}.
---

# pharaoh-finding-record

## When to use

Invoke from any audit subagent (`pharaoh-coverage-gap`, `pharaoh-lifecycle-check`, `pharaoh-standard-conformance`, `pharaoh-review-completeness`, `pharaoh-process-audit`) whenever the subagent has identified an issue that should be reported. Do NOT invoke for informational or non-actionable observations.

Do NOT invoke for new audit categories not in the known list — category must be one of: `orphan_arch`, `unverified_req`, `invalid_lifecycle_transition`, `duplicate_req`, `contradictory_req_pair`, `missing_fmea`, `stale_review`, `broken_back_link`, `schema_violation`, `wrong_prefix_id`, `missing_reviewer`, `missing_approval`.

## Atomicity

- (a) Indivisible — single write-or-dedup action. Does not audit, classify, or author.
- (b) Input: `{category: str, subject_id: str, finding_text: str, reporter_id: str}`. Output: `{action: "wrote"|"duplicate", papyrus_id: str, dup_of?: str}`.
- (c) Reward: deterministic — 2 reporters for same `(category, subject_id)` must produce exactly 1 `"wrote"` + 1 `"duplicate"` response; measured via fixture.
- (d) Reusable: any audit subagent; standalone CI gate; bug-tracking dedup.
- (e) Composable: Papyrus write-only; never modifies artefact files or invokes other skills.

## Input

- `category`: one of the known categories listed above.
- `subject_id`: the Score need ID affected by the finding (e.g. `arch__orphan_0`).
- `finding_text`: 1-3 sentence description. Used as the Papyrus need body.
- `reporter_id`: the calling subagent's area tag (e.g. `coverage-gap`, `lifecycle-check`). Stored in the Papyrus need `source` field for traceability.

## Output

A single-line JSON object, no prose:

`{"action": "wrote", "papyrus_id": "FACT_orphan_arch_arch_orphan_0"}`

or:

`{"action": "duplicate", "papyrus_id": "FACT_orphan_arch_arch_orphan_0", "dup_of": "FACT_orphan_arch_arch_orphan_0"}`

## Process

### Step 1: Construct deterministic ID

```
papyrus_id = "FACT_" + sanitize(category) + "_" + sanitize(subject_id)
```

`sanitize` replaces non-alphanumeric characters with underscores, collapses consecutive underscores, strips leading/trailing underscores. Example: `(orphan_arch, arch__orphan_0)` → `FACT_orphan_arch_arch_orphan_0`.

### Step 2: Attempt `papyrus add`

```bash
papyrus --workspace .papyrus add fact \
  "<short_title_from_finding_text>" \
  --id <papyrus_id> \
  --body <finding_text> \
  --tags "category:<category>,subject:<subject_id>" \
  --source "<reporter_id>" \
  --scope local
```

### Step 3: Interpret result

- Exit 0 → emit `{"action": "wrote", "papyrus_id": "<id>"}`.
- Exit non-zero with stderr containing `"already exists"` → emit `{"action": "duplicate", "papyrus_id": "<id>", "dup_of": "<id>"}`.
- Any other non-zero exit → emit `{"action": "error", "papyrus_id": "<id>", "message": "<stderr-first-line>"}` and return; the caller should not retry.

No surrounding prose. Emit exactly one JSON object per invocation.

## Dedup semantics

- Match key is `(category, subject_id)`. `finding_text` differences do NOT suppress dedup — the first writer wins and sets canonical phrasing.
- `reporter_id` difference does NOT suppress dedup — two subagents finding the same issue from different angles still collapse to one record.
- Concurrent writes for the same `papyrus_id` are serialized by the Papyrus `FileLock`; only one succeeds, the others get `"duplicate"`.

## Failure modes

- `papyrus` binary missing → emit `{"action": "error", "message": "papyrus CLI not found"}` and return.
- `.papyrus/` workspace missing → emit `{"action": "error", "message": "no .papyrus/ workspace in cwd"}`.
- Any other subprocess failure → emit `{"action": "error", "message": "<stderr-first-line>"}`.

## Composition

Each audit subagent invokes this skill once per finding. The orchestrator or harness then reads the final Papyrus workspace via `papyrus recall` for the aggregated report.

---
name: pharaoh-decision-record
description: Use when recording a canonical decision, fact, or preference in the shared Papyrus workspace with automatic dedup on (type, canonical_name). Returns {action: wrote|duplicate, papyrus_id}. Generalizes pharaoh-finding-record beyond audit findings.
---

# pharaoh-decision-record

## When to use

Invoke from any authoring or multi-agent coordination workflow that needs to record a canonical named item (architecture decision, domain fact, style preference) in a way that survives concurrent writers without duplication. Typical callers: `pharaoh-req-from-code` (when a type or concept is first surfaced), `pharaoh-decide` chains, multi-agent reverse-engineering fan-out.

Do NOT invoke for informational or non-canonical observations, and do NOT invoke when `pharaoh-finding-record` is a better fit (audit-finding category + subject_id tuple).

## Atomicity

- (a) Indivisible — single write-or-dedup action. Does not author, classify, or retrieve.
- (b) Input: `{type: "dec"|"fact"|"pref", canonical_name: str, body: str, tags?: list[str], reporter_id: str}`. Output: `{action: "wrote"|"duplicate"|"error", papyrus_id: str, dup_of?: str, message?: str}`.
- (c) Reward: deterministic — two writers for the same `(type, canonical_name)` must produce exactly 1 `"wrote"` + 1 `"duplicate"`; measured via fixture.
- (d) Reusable: any multi-agent workflow needing canonical-vocabulary coordination; ADR capture; design-decision dedup.
- (e) Composable: Papyrus write-only; never modifies artefact files or invokes other skills.

## Input

- `type`: one of `dec` (decision), `fact` (domain fact), `pref` (preference). Controls the Papyrus need type.
- `canonical_name`: canonical identifier for the subject. Style (snake_case, CamelCase, etc.) MUST match the frozen vocabulary if one exists for the project. If the caller is unsure, it MUST first invoke `pharaoh-context-gather` and reuse an existing canonical before coining a new one.
- `body`: 1-3 sentence description. Stored verbatim as the Papyrus need body.
- `tags`: optional list of free-form tags.
- `reporter_id`: caller identifier (e.g. `req-from-code:health_monitor.cpp`). Stored in the Papyrus need `source` field for traceability.

## Output

Exactly one single-line JSON object, no prose:

```json
{"action": "wrote", "papyrus_id": "FACT_HealthMonitor"}
```

or:

```json
{"action": "duplicate", "papyrus_id": "FACT_HealthMonitor", "dup_of": "FACT_HealthMonitor"}
```

or, on subprocess failure:

```json
{"action": "error", "papyrus_id": "FACT_HealthMonitor", "message": "<stderr-first-line>"}
```

## Process

### Step 1: Construct deterministic ID

```
papyrus_id = uppercase(type) + "_" + sanitize(canonical_name)
```

`sanitize` replaces non-alphanumeric characters with underscores, collapses consecutive underscores, strips leading/trailing underscores. Case is PRESERVED (do not lowercase).

Examples:
- `("fact", "HealthMonitor")` → `FACT_HealthMonitor`
- `("fact", "heartbeat_timeout")` → `FACT_heartbeat_timeout`
- `("dec", "use thread pool for monitors")` → `DEC_use_thread_pool_for_monitors`

### Step 2: Attempt `papyrus add`

```bash
papyrus --workspace .papyrus add <papyrus_need_type> \
  "<canonical_name>" \
  --id <papyrus_id> \
  --body "<body>" \
  --tags "canonical:<canonical_name>,<joined_tags>" \
  --source "<reporter_id>" \
  --scope local
```

The `<papyrus_need_type>` argument maps as: `dec` → `decision`, `fact` → `fact`, `pref` → `preference`.

### Step 3: Interpret result

- Exit 0 → emit `{"action": "wrote", "papyrus_id": "<id>"}`.
- Exit non-zero with stderr containing `"already exists"` → emit `{"action": "duplicate", "papyrus_id": "<id>", "dup_of": "<id>"}`.
- Any other non-zero exit → emit `{"action": "error", "papyrus_id": "<id>", "message": "<stderr-first-line>"}` and return; the caller must not retry.

No surrounding prose. Emit exactly one JSON object per invocation.

## Dedup semantics

- Match key is `(type, canonical_name)`. Body and tag differences do NOT suppress dedup — first writer wins and sets canonical body.
- `reporter_id` difference does NOT suppress dedup — two callers arriving at the same concept from different files still collapse to one record.
- Concurrent writes for the same `papyrus_id` are serialized by the Papyrus `FileLock`; only one succeeds, the others get `"duplicate"`.
- Case is significant in the ID: `FACT_HealthMonitor` and `FACT_healthmonitor` do NOT dedup. The caller is responsible for consistent casing (via `pharaoh-context-gather` lookup before coining).

## Failure modes

- `papyrus` binary missing → emit `{"action": "error", "message": "papyrus CLI not found"}`.
- `.papyrus/` workspace missing → emit `{"action": "error", "message": "no .papyrus/ workspace in cwd"}`.
- Any other subprocess failure → emit `{"action": "error", "message": "<stderr-first-line>"}`.

## Relationship to `pharaoh-finding-record`

`pharaoh-finding-record` is the audit-specialized sibling: it constrains `category` to a known enum and derives IDs from `(category, subject_id)`. `pharaoh-decision-record` accepts any `(type, canonical_name)` pair. Existing Phase 4b audit fan-out continues to use `pharaoh-finding-record`; Phase 4c's reverse-engineering fan-out uses `pharaoh-decision-record`.

A future cleanup may reimplement `pharaoh-finding-record` as a thin wrapper over `pharaoh-decision-record`; that refactor is out of scope for Phase 4c.

## Composition

Each caller invokes this skill once per canonical subject surfaced. The orchestrator or harness then reads the final Papyrus workspace via `papyrus recall` for the aggregated vocabulary.

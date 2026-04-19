---
name: pharaoh-audit-fanout
description: Orchestrator — run a full project audit by dispatching 5 atomic audit skills in parallel, each writing findings to a shared Papyrus workspace via pharaoh-finding-record for automatic deduplication. Emits the aggregated deduplicated findings list.
---

# pharaoh-audit-fanout

## When to use

Invoke at the start of a full project audit, CI gate, or pre-release review. Produces a deduplicated, terminology-consistent findings report covering 5 sub-areas in parallel.

## Compositional design (not atomic by design)

This is an orchestrator skill. Atomicity criteria (a) does not apply — the skill is compositional by construction. Its 5 component skills each pass (a)-(e) individually.

## Sub-areas

| # | Atomic skill | Target issues |
|---|---|---|
| 1 | `pharaoh-coverage-gap` | orphans, unverified req, uncovered req-verification |
| 2 | `pharaoh-lifecycle-check` | invalid state transitions, stale reviews |
| 3 | `pharaoh-standard-conformance` | ISO 26262 §6 / ASPICE indicator gaps |
| 4 | `pharaoh-review-completeness` | missing reviewer / approved_by fields |
| 5 | `pharaoh-process-audit` | duplicate req, contradictory pair, missing FMEA, broken back-link |

## Shared memory protocol

All 5 subagents write findings to the project's `.papyrus/` workspace using `pharaoh-finding-record`. The deterministic-ID scheme in `pharaoh-finding-record` provides natural dedup via Papyrus's `FileLock`-guarded ID-collision semantics.

Subagents SHOULD NOT retry on `action: duplicate` — that's the intended signal that another subagent already covered this issue.

## Process

### Step 1: Initialize workspace

Ensure `<project_dir>/.papyrus/` exists and is writable. If not, initialize via `papyrus --workspace <project_dir>/.papyrus init` (zero-config, silos preset).

### Step 2: Dispatch 5 subagents in parallel

In a production Pharaoh deployment, dispatch via Agent tool with `subagent_type: general-purpose`. In the Phase 4b harness, parallelism is achieved at the harness level via `concurrent.futures.ThreadPoolExecutor` over 5 separate `claude -p` invocations, each primed with one sub-area's task.

Each subagent receives:
- The project directory path
- Its assigned sub-area skill name (one of the 5)
- Explicit instruction to invoke `pharaoh-finding-record` for every finding

### Step 3: Aggregate

Once all 5 subagents complete, read the Papyrus workspace via:

```bash
papyrus --workspace <project_dir>/.papyrus recall --tag category:* --format full
```

Emit as the final audit report (JSON list of findings, ordered by category).

## Input / output

**Input:** `{project_dir: path, scope?: "full"|"partial"}`. Default scope is `full` (all 5 sub-areas). Partial scope limits to a subset of sub-areas (not used in Phase 4b testing).

**Output:** JSON list of aggregated findings, one object per `(category, subject_id)` pair:

```json
[
  {"category": "orphan_arch", "subject_id": "arch__orphan_0", "finding_text": "...", "reporter_id": "coverage-gap"},
  ...
]
```

## Failure modes

- `.papyrus/` workspace uninitializable → fall back to sequential single-agent `pharaoh-process-audit` with stderr warning.
- Any subagent errors → other 4 continue; final report notes the missing sub-area.
- >1 subagent timeout → abort and surface partial Papyrus state.

## Composition

Consumed by CI gates, on-demand user audits, and release governance workflows. Output is directly consumable by `pharaoh-audit-report` (future skill) or printed as-is.

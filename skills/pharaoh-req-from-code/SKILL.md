---
name: pharaoh-req-from-code
description: Use when reading one source file and emitting one or more comp_req RST directives describing the observable behavior in that file. Queries shared Papyrus for canonical terms before naming concepts; writes newly surfaced concepts back. Does not draft architecture, plans, or FMEA.
---

# pharaoh-req-from-code

## When to use

Invoke with a single C++ source file assigned to this agent and (optionally) a shared Papyrus workspace for cross-agent terminology coordination. Emit one comp_req per distinct observable behavior expressed in the file. Do NOT emit reqs for behavior not grounded in the file (that is drafting, not reverse-engineering). Do NOT attempt architecture, verification plans, or FMEA — those are separate skills.

## Atomicity

- (a) Indivisible — one file in → N reqs out. No I/O beyond file read + optional Papyrus query/write + RST emit.
- (b) Input: `{file_path: str, target_level: str, shared_context_path?: str, papyrus_workspace?: str, reporter_id: str}`. Output: list of RST `comp_req` directive blocks as strings, separated by blank lines.
- (c) Reward: fixture — given `test_fixture.cpp` containing exactly 3 named types (`FooBar`, `BazQux`, `Quux`), emitted reqs must mention all 3 by canonical name. Deterministic scorer via `concept_extractor`.
- (d) Reusable: any reverse-engineering workflow; standalone CI "are there reqs for this code?" gate; spec drafting.
- (e) Composable: strictly one phase. Never invokes `pharaoh-arch-draft`, `pharaoh-fmea`, `pharaoh-plan`, etc.

## Input

- `file_path`: absolute path to the C++ source file to reverse-engineer.
- `target_level`: the requirement artefact prefix (e.g. `comp_req` for component-level).
- `shared_context_path` (optional): path to a companion source file read by all agents in the fan-out (e.g. `common.cpp`). Read but NOT reverse-engineered into reqs by this agent.
- `papyrus_workspace` (optional): path to `.papyrus/` directory for canonical-term coordination. If omitted, the skill operates in no-memory mode (does not call `pharaoh-context-gather` or `pharaoh-decision-record`).
- `reporter_id`: short identifier for this agent (e.g. `req-from-code:health_monitor.cpp`). Passed to `pharaoh-decision-record` calls.

## Output

Zero or more RST `comp_req` directive blocks, one behavior per block. Each block:

```
.. comp_req:: <short_title>
   :id: comp_req__<snake_case_id>
   :status: draft

   The <subject> shall <observable_behavior>.
```

Blocks are separated by one blank line. No surrounding prose outside the blocks, no final summary.

## Process

### Step 1: MANDATORY — query Papyrus for canonical terms BEFORE naming anything

**Hard prompt clause (load-bearing for cross-agent first-writer-wins):**

> Before naming any type, function, or concept in your emitted reqs, call `pharaoh-context-gather` with a semantic query describing the concept. If a canonical name already exists in Papyrus, use it verbatim — do not coin synonyms or variants.

Only applies if `papyrus_workspace` is provided. For each type / function / entity you observe in the file that you might name in a req:

1. Form a short semantic query (e.g. "what do we call the subsystem that supervises other monitors").
2. Invoke `pharaoh-context-gather` with that query against `papyrus_workspace`.
3. If a matching canonical appears in the top-3 results, use that exact spelling in your req (preserve case exactly — e.g. `HealthMonitor` not `health_monitor`).
4. If no match, plan to introduce a new canonical name in Step 3.

### Step 2: Read the source file

Read `file_path` and, if provided, `shared_context_path`. Identify observable behaviors: things the code DOES that a spec could describe, grounded in the actual control flow and data flow in the file. Ignore implementation detail that is not observable at the component boundary (internal helpers, log messages, assertion text).

### Step 3: Record newly surfaced concepts in Papyrus

Only applies if `papyrus_workspace` is provided. For each type / function / concept that (a) you will mention in a req and (b) was NOT already returned by Step 1, invoke `pharaoh-decision-record` with:

- `type`: `"fact"`
- `canonical_name`: your chosen name in the code's native casing style (preserve CamelCase for types, snake_case for functions/fields)
- `body`: one sentence describing the concept
- `reporter_id`: your `reporter_id` input
- `tags`: `["origin:req-from-code", "file:<basename>"]`

If `pharaoh-decision-record` returns `"duplicate"`, that means a concurrent agent raced you to that canonical; in that case re-query via `pharaoh-context-gather`, adopt the existing canonical spelling, and rewrite your draft req(s) to use it.

### Step 4: Emit comp_req directives

For each observable behavior in the file, emit one `comp_req` block:

- `<short_title>` — 3-6 word summary.
- `:id: comp_req__<snake_case_id>` — include file basename as a disambiguator: `comp_req__<filename_stem>_<n>`, e.g. `comp_req__deadline_monitor_01`.
- Body — one sentence, single `shall` clause, using canonical names from Steps 1/3 (preserve original casing).

Target: 1-5 reqs per file. Fewer than 1 only if the file has no observable behavior (e.g. pure private implementation detail); more than 5 suggests the skill is being asked to over-decompose — stop at 5 and defer.

### Step 5: Return

Return the concatenation of directive blocks with blank-line separators. No prose.

## No-memory mode (when `papyrus_workspace` is absent)

Skip Steps 1 and 3. Proceed directly to Steps 2, 4, 5. This is how variant C exercises the skill.

## Failure modes

- `file_path` not readable → return empty output (no reqs).
- `pharaoh-context-gather` errors → log and proceed as if no match found (do not abort).
- `pharaoh-decision-record` returns `"error"` (not `"duplicate"`, which is normal) → log and proceed. Do not retry.

## Composition

Orchestrator `pharaoh-reqs-from-module` dispatches N instances of this skill in parallel, one per file in the module's source directory, sharing the same `papyrus_workspace`.

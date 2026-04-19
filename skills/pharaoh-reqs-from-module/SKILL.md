---
name: pharaoh-reqs-from-module
description: Orchestrator — reverse-engineer comp_reqs for an entire module by dispatching pharaoh-req-from-code in parallel, one agent per source file, sharing a Papyrus workspace for cross-agent terminology coordination. Aggregates into a single RST document.
---

# pharaoh-reqs-from-module

## When to use

Invoke when the user wants comp_req coverage for a bounded subsystem (one directory of cohesive source files) and wants cross-file terminology consistency. Works best on 3-8 files totaling up to ~1000 LOC.

## Compositional structure (not atomic by design)

This skill is explicitly a COMPOSITION of other atomic skills. It does not add new reward-mechanizable behavior of its own; it coordinates other atomics. Therefore it is exempt from criterion (a) (indivisibility) per the atomic-skills refactor. The constituent atomics (`pharaoh-context-gather`, `pharaoh-req-from-code`, `pharaoh-decision-record`) each pass (a)-(e).

## Input

- `module_dir`: directory containing the source files to reverse-engineer.
- `file_list`: list of filenames (relative to `module_dir`) to assign one-per-agent.
- `shared_context_file` (optional): a file all agents read for shared context but none reverse-engineers.
- `target_level`: requirement artefact prefix (e.g. `comp_req`).
- `papyrus_workspace`: path to `.papyrus/` workspace (may be empty or preseeded).

## Output

A single RST document concatenating all emitted `comp_req` directives from all agents, with a section header per source file for human readability.

## Process (reference orchestration)

### Step 1: Prepare Papyrus workspace

If `papyrus_workspace` does not exist, initialize it empty. If preseeding is desired (variant B_seeded), the CALLER is responsible for doing so before invoking this orchestrator.

### Step 2: Dispatch N parallel agents

For each file in `file_list`, dispatch one instance of `pharaoh-req-from-code` with:
- `file_path = module_dir / file`
- `shared_context_path = module_dir / shared_context_file` (if provided)
- `papyrus_workspace` (passed through)
- `reporter_id = "req-from-code:" + file`

Agents MUST run concurrently so that first-writer-wins ordering in Papyrus is exercised.

### Step 3: Aggregate

Concatenate agent outputs into one document with per-file section headers. Do NOT filter duplicates at this layer; dedup is a scoring concern, not an orchestration concern.

## Harness-driven variant

In Phase 4c measurement, parallel dispatch happens in `pharaoh-validation/harness/run_phase4c.py`, not inside an agent running this skill. Reason: clean measurement and cost attribution. Future versions may move dispatch into an in-agent MCP subagent call — this SKILL.md is the spec for that.

## Non-goals

- No fan-out to other phases (arch, vplan, fmea) — that is a separate orchestrator.
- No cross-module coordination — one module per invocation.
- No output filtering or dedup — done downstream in scoring or integration.

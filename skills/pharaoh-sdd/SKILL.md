---
name: pharaoh-sdd
description: Use when a developer wants to add a feature, capability, or behaviour change to a project that uses sphinx-needs and a V-model artefact structure, before any requirement or code is written. Triggers on "add a feature", "implement X", "let's build Y", or "do spec-driven development" in a project with .pharaoh/project/ tailoring.
chains_from: []
chains_to: []
---

# pharaoh-sdd

## Overview

The graph is not the hard part. An agent will happily produce one. The hard part is not
fabricating it. Requirements come from the human, every artefact carries its review, and
every tier builds clean before the next. This skill enforces that contract.

## Composition

pharaoh-sdd is a non-atomic orchestrator. It does not draft or review artefacts directly.
It dispatches the following atomic skills:

- `pharaoh-req-draft`: drafts requirement-shaped artefacts at any catalog-declared level
- `pharaoh-arch-draft`: drafts architecture artefacts
- `pharaoh-vplan-draft`: drafts verification plans and test cases
- `pharaoh-req-codelink-annotate`: links implemented code back into the requirement graph
- `pharaoh-quality-gate`: verifies review coverage and trace completeness at the end

Each `*-draft` skill self-invokes its matching `*-review` as its last step and returns
`{artefact, review}`. The orchestrator reads that review. It does NOT call `*-review`
again for a freshly drafted artefact.

## The Iron Gate

Do NOT draft tier N+1 until tier N is drafted, reviewed, validated with `sphinx-build -W`,
and approved by the human. This holds for every project no matter how small the feature.

Violating the letter of this gate is violating the spirit of it.

## When to use

- A developer asks to add a feature, capability, or behaviour change.
- The project has `.pharaoh/project/` tailoring and a sphinx-needs V-model.
- Use even for tiny features. Small features are where requirements get silently invented.

When NOT to use: pure refactors, bug fixes against an existing requirement, or projects
with no sphinx-needs structure.

## Input

- The developer's feature intent in prose (what, why, measurable success criteria).
- The project root path.
- `.pharaoh/project/` tailoring: `artefact-catalog.yaml`, `id-conventions.yaml`, lifecycle
  config, and any domain-specific checklists.
- `pharaoh.toml` at the project root and `.pharaoh/project/` tailoring (inputs for deriving
  tier order, described in Phase 1 below).

## Output

- A set of linked sphinx-needs artefacts forming the V-model graph, one per tier.
- A clean `sphinx-build -W` after each tier.
- A pharaoh-quality-gate verdict with review coverage confirmed for every drafted artefact.

## Process

### Phase 0: Elicitation

Before drafting anything. This is a dialogue, not a form.

1. Read project context: `.pharaoh/project/` tailoring (types, tiers, lifecycle),
   `pharaoh.toml`, and a sample of recent needs from the corpus.
2. Ask the developer clarifying questions ONE at a time: purpose, constraints, success
   criteria, and every parameter value that would otherwise be guessed.
3. Decompose the feature into individual requirements and present that decomposition.
4. Gate: the developer approves the requirement list. No invented value survives into
   a requirement.

### Phase 1 onward: walk the V-model tiers

Create a run directory at `.pharaoh/runs/<timestamp>/` before the first tier. Use it for
all review JSON written during the tier loop. The Terminal step passes this directory to
`pharaoh-quality-gate`.

Derive the V-model tier order by checking these sources in priority order. First, look for
an explicit tier or chain declaration in `pharaoh.toml` or `.pharaoh/project/`. If none
exists, topologically sort the `required_links` chain pairs from `[pharaoh.traceability]`
when they cover all tiers in use. If that is still incomplete, infer the order from the
artefact-catalog types together with the link structure observed in the existing corpus
(`needs.json`). Present the derived tier order to the developer and get confirmation before
any drafting begins.

Do not hardcode tier depth. For each tier, in order, run this loop:

| step | action |
|------|--------|
| draft | Dispatch the tier's atomic draft skill once per artefact. The draft skill self-invokes its review and returns `{artefact, review}`. |
| evaluate | Read the attached review. If `overall: fail`, `overall: needs_work`, or any binary axis has `score: 0`, re-dispatch the draft skill with the review action items folded into the description. Use `pharaoh-req-regenerate` for requirements, re-invoke the draft skill directly for arch and vplan. |
| normalise | If the project traces with a generic link field (read from `ubproject.toml [needs.links]` and the existing corpus), rewrite the drafted directive's typed link option (`:satisfies:` or `:verifies:`) to that field. If `ubproject.toml` is absent or has no `[needs.links]` table, keep the typed link as-is. |
| persist | Write the artefact into the docs tree. Write its review JSON into the run directory so `pharaoh-quality-gate` can confirm review coverage. |
| rebuild | Run `sphinx-build -W` on the docs. The tier is not done until the build is clean and `needs.json` regenerates with the new needs. |
| checkpoint | Present the tier's artefacts to the developer. Get approval before the next tier. |

At the implementation tier the agent writes the code directly, following test-driven
development practice (write the failing test first, then make it pass, then refactor). No
Pharaoh atomic skill governs this tier. Once the implementation is complete, run
`pharaoh-req-codelink-annotate` with `file_path`, `anchor`, `project_root`, and `mode`
supplied to link the finished code back into the requirement graph.

### Terminal

Aggregate the persisted review JSONs into the summary YAML that `pharaoh-quality-gate`
expects. Run `pharaoh-quality-gate`. The deliverable is a V-model graph where every tier
traces to the next, every artefact has a review on disk, and the build is clean.

## The baseline this skill exists to stop

Handed "add feature X, do spec-driven development" without this skill, an agent will:

- Invent the requirements itself, with fabricated thresholds, parameters, and acceptance
  criteria, instead of eliciting them from the developer.
- Run requirement, design, test, and code in one unattended pass with no human in the loop.
- Draft every artefact and review none.
- Build once at the end without `-W`, accepting warnings silently.

Each of those is a defect. The process above closes them.

## Rationalisations: STOP

| Excuse | Reality |
|--------|---------|
| "I can infer the parameters myself." | An inferred parameter is a fabricated requirement. Elicit it. |
| "The build succeeded, it is fine." | A build without `-W` passes on warnings. Run `-W`. |
| "The draft already passed, skip the review." | The draft skill attaches a review. Read it. `overall: needs_work` triggers a re-dispatch just as `fail` does. |
| "It is a small feature, skip the gate." | Small features are where requirements get invented. The gate holds. |
| "Running the whole chain is faster." | An unattended chain bakes in decisions the developer never approved. Stop at every checkpoint. |

## Red flags: STOP and return to the last passed gate

- About to write a requirement value the developer never gave you.
- About to draft tier N+1 while tier N has a `fail`, `needs_work`, or `score: 0` review.
- About to move past a tier with `sphinx-build` warnings.
- Ran draft, design, and test with no human pause between them.

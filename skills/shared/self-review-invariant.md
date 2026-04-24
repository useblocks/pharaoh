# Self-review invariant

Shared invariant for every Pharaoh skill that emits an artefact (draft, extract, record, annotation).

## The rule

Before returning success, an emission skill MUST arrange for its matching review skill (see `shared/self-review-map.yaml`) to run against the emitted artefact. This applies in three operating contexts:

1. **Invoked via a plan** (`pharaoh-execute-plan`): the plan DAG must contain a `*_review` task that depends on the `*_draft` task. `pharaoh-write-plan` enforces this when templating.
2. **Invoked ad-hoc outside a plan**: the emission skill's "Last step" instructs the caller (human or agent) to invoke the mapped review skill and attach the review JSON alongside the emitted artefact.
3. **Invoked by another orchestrator skill**: the orchestrator is responsible for calling the mapped review skill before returning success.

In all three contexts, the `pharaoh-self-review-coverage-check` invariant (wired into `pharaoh-quality-gate`) detects violations after the fact.

## Why it exists

Reviewing drafts is possible via the per-artefact review skills (`pharaoh-req-review`, `pharaoh-arch-review`, `pharaoh-vplan-review`, `pharaoh-feat-review`, `pharaoh-fmea-review`, `pharaoh-decision-review`, `pharaoh-diagram-review`). But dogfooding surfaced that an LLM running a plan end-to-end routinely skips review tasks as a cost-saving improvisation. The invariant upgrades "review is available" to "review always runs and its absence is a gate failure".

## How emission skills reference this

Every emission skill's body includes a **Last step** section of the form:

```markdown
## Last step

After emitting the artefact, invoke `pharaoh-<TYPE>-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output as `review: <findings JSON>`. See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale and enforcement mechanism.
```

with `<TYPE>` resolved via `shared/self-review-map.yaml`.

## Failure closed vs failure open

Self-review is **failure-closed** on critical findings. If the review emits any axis with `score: 0` (failing, per ISO 26262 §6 rubric) or explicit `severity: critical`, the emission skill returns a non-success status with the review findings verbatim. Non-critical findings (score ≥ 1 or informational) do not fail emission — they are attached to the output for the reviewer to act on.

## Exclusions

Skills that do NOT emit artefacts are not in scope:

- Validators (`pharaoh-output-validate`, `pharaoh-diagram-lint`)
- Gates (`pharaoh-quality-gate`)
- Checks (`pharaoh-papyrus-non-empty-check`, `pharaoh-dispatch-signal-check`, `pharaoh-self-review-coverage-check`, `pharaoh-lifecycle-check`, `pharaoh-review-completeness`)
- Retrieval (`pharaoh-context-gather`, `papyrus-query`, `papyrus-drill`)
- ID allocation (`pharaoh-id-allocate`)
- The review skills themselves (they ARE the review)

Shared references (not skills): `shared/diagram-safe-labels.md`, `shared/uml-relationship-semantics.md`, `shared/data-access.md`, `shared/strictness.md` — out of scope.

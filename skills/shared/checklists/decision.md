---
name: decision
applies_to: decision
axes:
  - context_section_present
  - alternatives_listed
  - consequences_section_present
  - trace_to_affected_artefacts
  - canonical_name_unique
  - rationale_quality
---

# Decision review checklist

Generic baseline for reviewing a single recorded decision (DR / ADR / design note).

## Mechanized axes

### context_section_present
Body contains a `Context` section heading (`Context\n-------` or `**Context:**`).

### alternatives_listed
Body contains an `Alternatives` section with at least two bullet items OR an explicit "alternatives considered" table.

### consequences_section_present
Body contains a `Consequences` section (positive + negative bullets, or prose).

### trace_to_affected_artefacts
Directive has at least one outgoing link (`:affects:`, `:supersedes:`, `:relates_to:`, or the project's declared decision-link option) that resolves.

### canonical_name_unique
If the decision is Papyrus-backed, the `(type, canonical_name)` tuple appears exactly once in the Papyrus workspace. Mechanical dedup check.

## Subjective axis

### rationale_quality (0-3)
- 3 — Rationale names the driving constraint or value and ties it explicitly to the chosen alternative.
- 2 — Rationale present but weak link to the choice.
- 1 — Rationale restates the choice without justification.
- 0 — Rationale missing or placeholder.

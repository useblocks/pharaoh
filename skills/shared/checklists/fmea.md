---
name: fmea
applies_to: fmea
axes:
  - trace_to_analyzed_artefact
  - severity_in_range
  - occurrence_in_range
  - detection_in_range
  - rpn_computed_correctly
  - cause_well_formed
  - effect_well_formed
  - mitigation_proposed_if_rpn_high
---

# FMEA review checklist

Generic baseline for reviewing a single FMEA row.

## Mechanized axes

### trace_to_analyzed_artefact
FMEA entry has `:analyzes:` or `:satisfies:` linking to the requirement / architecture element under analysis. Orphan FMEA → fail.

### severity_in_range / occurrence_in_range / detection_in_range
Each of S/O/D is integer within the configured scale (default 1..10). Scale tailorable via `.pharaoh/project/artefact-catalog.yaml > fmea > scales`.

### rpn_computed_correctly
`rpn == severity * occurrence * detection`. Recompute; fail on mismatch.

### mitigation_proposed_if_rpn_high
If `rpn >= threshold` (default 60, tailorable), a `:mitigation:` field must be present and non-empty. Below threshold: mitigation optional.

## Subjective axes

### cause_well_formed (0-3)
- 3 — Root cause named, not a symptom; physically / logically plausible.
- 2 — Cause named but at symptom level.
- 1 — Cause vague or circular.
- 0 — Cause missing or unparseable.

### effect_well_formed (0-3)
- 3 — Effect describes observable external consequence (functional, safety, security).
- 2 — Effect partially internal.
- 1 — Effect is a synonym of the failure mode itself.
- 0 — Effect missing or unparseable.

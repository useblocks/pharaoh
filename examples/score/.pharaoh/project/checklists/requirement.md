---
name: Requirement inspection checklist (Score-tailored ISO 26262-8 §6)
applies_to: gd_req
axes:
  - schema
  - unambiguity_prose
  - comprehensibility
  - atomicity
  - internal_consistency
  - feasibility
  - verifiability
  - completeness
  - external_consistency
  - no_duplication
  - maintainability
---

# Requirement inspection checklist (Score-tailored ISO 26262-8 §6)

## Individual
- [ ] schema: requirement uses the expected need structure and required fields
- [ ] unambiguity_prose: single clear meaning; single `shall`; no coordinating conjunctions within the shall clause
- [ ] comprehensibility: reader at adjacent abstraction (consumer/producer) understands without additional context
- [ ] atomicity: cannot be split into 2 requirements at this level (1 `shall`, no conjunction)
- [ ] internal_consistency: no self-contradiction within this requirement
- [ ] feasibility: implementable within item-development constraints; no obvious infeasibility
- [ ] verifiability: :verification: or :satisfied_by: link present AND resolves

## Set
- [ ] completeness: every parent requirement has ≥ 1 child
- [ ] external_consistency: no pair of requirements contradict each other
- [ ] no_duplication: no two req bodies below 0.15 cosine distance
- [ ] maintainability: set survives regeneration (fixed point within 2 iterations)

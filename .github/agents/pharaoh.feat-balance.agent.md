---
description: Use when a plan emitted by `pharaoh-write-plan` has completed its feature + comp_req emission and you need to check for granularity skew — features with too many reqs (under-decomposed feature model), too few (over-decomposed), fused sub-features (generic names like "utilities"), or redundancy (symmetric import/export pairs). Reports health and suggestions; does not mutate.
handoffs: []
---

# @pharaoh.feat-balance

Use when a plan emitted by `pharaoh-write-plan` has completed its feature + comp_req emission and you need to check for granularity skew — features with too many reqs (under-decomposed feature model), too few (over-decomposed), fused sub-features (generic names like "utilities"), or redundancy (symmetric import/export pairs). Reports health and suggestions; does not mutate.

See [`skills/pharaoh-feat-balance/SKILL.md`](../../skills/pharaoh-feat-balance/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

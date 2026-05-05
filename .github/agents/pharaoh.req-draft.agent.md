---
description: Use when drafting a single sphinx-needs requirement-shaped artefact (req, comp_req, sysreq, swreq, hazard, safety_goal, fsr, etc.) from a feature description. The artefact type is parameterised via target_level (any catalog-declared requirement-shaped type, including ISO 26262 safety-V types). Produces a new RST directive block with ID, status=draft, and either a shall-clause body or a hazard/goal-shaped body, linking to a parent per the project's artefact-catalog.
handoffs: []
---

# @pharaoh.req-draft

Use when drafting a single sphinx-needs requirement-shaped artefact (req, comp_req, sysreq, swreq, hazard, safety_goal, fsr, etc.) from a feature description. The artefact type is parameterised via target_level (any catalog-declared requirement-shaped type, including ISO 26262 safety-V types). Produces a new RST directive block with ID, status=draft, and either a shall-clause body or a hazard/goal-shaped body, linking to a parent per the project's artefact-catalog.

See [`skills/pharaoh-req-draft/SKILL.md`](../../skills/pharaoh-req-draft/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

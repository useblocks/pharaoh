---
description: Use when orchestrating the full V-model chain for one feature context across the optional ISO 26262 safety V (hazard / safety_goal / fsr), the ASPICE SYS layer (sysreq / sys-arch), the ASPICE SW layer (swreq / swarch), and the classical component V (req / comp_req then arch then vplan then fmea), each with a review pass. Auto-detects which layers to run from the project's artefact-catalog.yaml; the caller can pass a stages argument to skip layers explicitly. Dispatches to pharaoh-req-draft, pharaoh-req-review, pharaoh-arch-draft, pharaoh-arch-review, pharaoh-vplan-draft, pharaoh-vplan-review, and pharaoh-fmea — safety-V types route through pharaoh-req-draft with the appropriate target_level, no new safety-V drafting skills are introduced.
handoffs: []
---

# @pharaoh.flow

Use when orchestrating the full V-model chain for one feature context across the optional ISO 26262 safety V (hazard / safety_goal / fsr), the ASPICE SYS layer (sysreq / sys-arch), the ASPICE SW layer (swreq / swarch), and the classical component V (req / comp_req then arch then vplan then fmea), each with a review pass. Auto-detects which layers to run from the project's artefact-catalog.yaml; the caller can pass a stages argument to skip layers explicitly.

Dispatches to pharaoh-req-draft, pharaoh-req-review, pharaoh-arch-draft, pharaoh-arch-review, pharaoh-vplan-draft, pharaoh-vplan-review, and pharaoh-fmea. Safety-V types route through pharaoh-req-draft with the appropriate target_level (hazard, safety_goal, fsr) — no new safety-V drafting skills are introduced.

See [`skills/pharaoh-flow/SKILL.md`](../../skills/pharaoh-flow/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

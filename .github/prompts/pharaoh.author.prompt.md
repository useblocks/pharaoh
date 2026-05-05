---
agent: pharaoh.author
---

# /pharaoh.author

Author or modify one sphinx-needs artefact — a requirement, an architecture element, a test
case, or a decision — by routing to the right atomic drafting skill based on the project's
artefact catalog. One invocation produces one drafted RST directive with an ID, a parent link,
and a suggested file placement.

Hand the agent:

- the **target type** (e.g. `req`, `arch`, `tc`, `decision`),
- a short **draft seed** describing what to author,
- the **parent link** the new artefact will trace to (need-id), and
- any type-specific extras the dispatched drafter needs (e.g. `arch_type`,
  `verification_level`).

The agent picks the matching atomic drafter (`pharaoh-req-draft`, `pharaoh-arch-draft`,
`pharaoh-vplan-draft`, or `pharaoh-decide`), forwards the inputs, and returns the drafted RST
directive plus an authoring summary. Run `@pharaoh.verify` next to check the new artefact
against the substance of its parent.

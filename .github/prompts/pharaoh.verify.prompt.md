---
agent: pharaoh.verify
---

# /pharaoh.verify

Check whether one sphinx-needs artefact actually addresses the substance of every parent it
links to via `:satisfies:` or `:verifies:`. This is a cross-need content check — distinct from
structural MECE (`@pharaoh.mece`), schema-level tailoring review (`@pharaoh.tailor-review`),
and per-axis prose review (`@pharaoh.req-review`, `@pharaoh.arch-review`,
`@pharaoh.vplan-review`).

Hand the agent:

- the **need-id** to verify, and
- optionally `transitive: true` to walk the full parent chain rather than just direct parents.

The agent reads `needs.json`, walks the parent links, scores each (child, parent) pair on a
0-3 ordinal for substantive coverage, and returns a JSON document with per-pair verdicts and
concrete missing aspects. Use the result to decide whether to re-author the body via
`@pharaoh.author`, regenerate it per-axis via `@pharaoh.req-regenerate`, or move on to a
corpus-wide check with `@pharaoh.mece`.

# list-mapped-complete

Exercises the list-valued branch of the detection rule with a complete invocation set. The emission skill `pharaoh-req-from-code` maps to the two-element list `[pharaoh-req-review, pharaoh-req-code-grounding-check]`, and both review skills are invoked in the emission skill's `## Last step` section. Expected output: `passed: true` with an empty `uncovered` list. Pairs with `list-mapped-partial/` which removes one invocation to force a failure.

# list-mapped-partial

Exercises the failure path of the list-valued branch. The emission skill `pharaoh-req-from-code` maps to `[pharaoh-req-review, pharaoh-req-code-grounding-check]` but only the first review is invoked in its `## Last step`. Expected output: `passed: false` with a single `uncovered` entry naming `pharaoh-req-code-grounding-check` as the missing `expected_review_skill`. Demonstrates that a partial invocation of a list-valued map fails with a specific missing entry rather than a generic mismatch.

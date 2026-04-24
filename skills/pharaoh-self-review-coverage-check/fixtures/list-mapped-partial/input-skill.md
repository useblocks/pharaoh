---
name: pharaoh-req-from-code
description: Stub emission SKILL.md used as fixture input — only the `## Last step` section is load-bearing. Here only one of the two expected review skills is invoked, so the coverage check must fail.
---

# pharaoh-req-from-code

## Last step

After emitting the artefact, invoke `pharaoh-req-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`.

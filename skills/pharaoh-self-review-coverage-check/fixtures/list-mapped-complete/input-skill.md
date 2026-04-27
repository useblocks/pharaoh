---
name: pharaoh-req-from-code
description: Stub emission SKILL.md used as fixture input — only the frontmatter and the `## Last step` section are load-bearing for the coverage check.
---

# pharaoh-req-from-code

## Last step

After emitting the artefact, invoke `pharaoh-req-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`.

Additionally, for each emitted CREQ that has `:source_doc:`, invoke `pharaoh-req-code-grounding-check`. Attach its findings JSON under the key `code_grounding`. If either atom returns a mechanised-axis failure, do NOT finalize the artefact.

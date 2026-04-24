---
name: pharaoh-req-draft
description: Stub emission SKILL.md used as fixture input for backward-compatibility. Scalar-valued mapping — one review skill invoked in `## Last step`.
---

# pharaoh-req-draft

## Last step

After emitting the artefact, invoke `pharaoh-req-review` on it. Pass the emitted artefact (or its `need_id`) as `target`. Attach the returned review JSON to the skill's output under the key `review`.

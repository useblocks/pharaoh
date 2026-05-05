---
description: Use when verifying that every need id in a sphinx-needs corpus matches the regex declared for its type in `.pharaoh/project/id-conventions.yaml`. Single mechanical structural check — applies the tailored per-type regex, emits a list of violations. Does NOT auto-detect how many schemes coexist — scheme policy is the tailoring author's responsibility (declare an alternation to allow multiple forms).
handoffs: []
---

# @pharaoh.id-convention-check

Use when verifying that every need id in a sphinx-needs corpus matches the regex declared for its type in `.pharaoh/project/id-conventions.yaml`. Single mechanical structural check — applies the tailored per-type regex, emits a list of violations. Does NOT auto-detect how many schemes coexist — scheme policy is the tailoring author's responsibility (declare an alternation to allow multiple forms).

See [`skills/pharaoh-id-convention-check/SKILL.md`](../../skills/pharaoh-id-convention-check/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

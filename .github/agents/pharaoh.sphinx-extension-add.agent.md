---
description: Use when you need to idempotently add one or more sphinx extension modules to a project's `conf.py` extensions list, optionally installing the corresponding pypi packages via the detected package manager. Invoked by plans produced by pharaoh-write-plan when a diagram-emitting task requires a renderer extension that `conf.py` does not yet load. Does NOT emit RST. Does NOT build.
handoffs: []
---

# @pharaoh.sphinx-extension-add

Use when you need to idempotently add one or more sphinx extension modules to a project's `conf.py` extensions list, optionally installing the corresponding pypi packages via the detected package manager. Invoked by plans produced by pharaoh-write-plan when a diagram-emitting task requires a renderer extension that `conf.py` does not yet load. Does NOT emit RST. Does NOT build.

See [`skills/pharaoh-sphinx-extension-add/SKILL.md`](../../skills/pharaoh-sphinx-extension-add/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

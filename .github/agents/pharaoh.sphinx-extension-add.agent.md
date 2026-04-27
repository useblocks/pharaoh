---
description: Idempotently add one or more sphinx extension modules to a project's `conf.py` extensions list, optionally installing the corresponding pypi packages via the detected package manager.
handoffs: []
---

# @pharaoh.sphinx-extension-add

Add sphinx extensions (e.g. `sphinxcontrib.mermaid`, `sphinxcontrib.plantuml`, `myst_parser`) to a project's `conf.py` extensions list. Idempotent: noop when all requested extensions are already loaded. Optionally installs the corresponding pypi packages via the detected package manager (rye / uv / poetry / pdm / pip-venv). Typically inserted into a plan by `pharaoh.write-plan` as a prerequisite to diagram-emitting tasks when `conf.py` lacks the required renderer extension.

See [`skills/pharaoh-sphinx-extension-add/SKILL.md`](../../skills/pharaoh-sphinx-extension-add/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

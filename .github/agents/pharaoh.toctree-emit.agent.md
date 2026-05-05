---
description: Use when a composition skill has just emitted a set of RST files into a directory and needs to add (or regenerate) an `index.rst` with a Sphinx toctree over them. Prevents orphan-file warnings under `sphinx-build -W`. Does NOT modify the emitted RST files. Does NOT wire the emitted directory into any parent toctree — that is a caller concern.
handoffs: []
---

# @pharaoh.toctree-emit

Use when a composition skill has just emitted a set of RST files into a directory and needs to add (or regenerate) an `index.rst` with a Sphinx toctree over them. Prevents orphan-file warnings under `sphinx-build -W`. Does NOT modify the emitted RST files. Does NOT wire the emitted directory into any parent toctree — that is a caller concern.

See [`skills/pharaoh-toctree-emit/SKILL.md`](../../skills/pharaoh-toctree-emit/SKILL.md) for the full atomic specification — inputs, outputs, atomicity contract, and composition patterns.

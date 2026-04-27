# python-non-behavioral-reexport

Re-export-only `__init__.py`: imports, module-level constants, and an `__all__` list. No function bodies, no raises, no classes. Classifier output is `non-behavioral`; both sub-axes are emitted with `passed: null` (not applicable). Expected verdict: `overall: "skipped"` — the file never fails the coverage gate because there is no behavior for the catalogue to cover.

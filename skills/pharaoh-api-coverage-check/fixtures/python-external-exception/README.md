# python-external-exception

Exercises the project-definition scan. `input-source.py` raises two
classes: `CatalogError` (defined in `errors.py` within the fixture's
`project_root` scope) and `ValueError` (Python stdlib — not defined
anywhere under `project_root`).

The CREQ catalogue names `CatalogError` but not `ValueError`. The
fixture passes because `project_defined` is `1` (CatalogError),
`covered` is `[CatalogError]`, `uncovered` is `[]`, and `ValueError`
is surfaced in `external` as diagnostic-only.

Invocation: `source_file=input-source.py, needs_json_path=input-needs.json, project_root=<fixture_dir>`.

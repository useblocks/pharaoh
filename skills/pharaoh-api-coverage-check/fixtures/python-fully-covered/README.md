# python-fully-covered

Canonical Python happy path. The source file raises `InventoryError` (behavioral via the exception-surface rule) and declares `class InventoryClient` with two methods (behavioral via the method-rich-class rule). Four needs cite the file via `:source_doc:` and the body of one need names `InventoryError`. Expected verdict: `overall: "pass"`.

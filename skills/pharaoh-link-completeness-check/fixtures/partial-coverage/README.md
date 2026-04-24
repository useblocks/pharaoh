# partial-coverage

Exercises the three failure modes of this atom:

1. `comp_req__billing_refund` is missing the `:verifies:` key entirely — counted as missing.
2. `comp_req__billing_dispute` has `verifies: []` — empty list also counts as missing.
3. `comp_req__billing_export` carries a non-empty `verifies` but its only target (`tc__does_not_exist`) is not in `needs.json` — recorded in `unresolved_targets`.

`tc` coverage is computed on `tc__billing_invoice_ok` alone (one of four reqs has a matching tc). `satisfies` is fully covered because every `comp_req` points at `feat__billing`, which exists.

Expected: `overall: "fail"`, `coverage_by_link_type.verifies.missing == 2`, two ids in `uncovered_needs` (deduplicated, sorted), one entry in `unresolved_targets`.

# tailoring-declares-verifies-optional

Demonstrates the one tailoring lever: moving `verifies` from `required_links` to `optional_links` on `comp_req` downgrades its absence from a gate failure to an informational metric.

Both `comp_req` needs omit `:verifies:`. Because the catalog marks it optional, `coverage_by_link_type.verifies.required` is `false` and the two missing values do not populate `uncovered_needs` nor flip `overall`. `satisfies` remains required and both reqs carry it, so the gate passes.

Expected: `overall: "pass"`, `verifies.required: false`, `verifies.missing: 2` (informational), `uncovered_needs` empty, `unresolved_targets` empty.

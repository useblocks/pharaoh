# all-covered

Canonical happy path. The catalog declares `satisfies` and `verifies` required for `comp_req`, and `verifies` required for `tc`. Every `comp_req` in the corpus carries both links with non-empty lists, every `tc` carries `verifies`, and every target id resolves to an existing need. `feat` has no required outgoing links so it contributes to `needs_checked` but to no coverage row.

Expected: `overall: "pass"`, zero `missing` across `coverage_by_link_type`, empty `uncovered_needs`, empty `unresolved_targets`.

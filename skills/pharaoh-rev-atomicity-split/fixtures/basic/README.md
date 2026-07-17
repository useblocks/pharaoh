# basic

`input-need.json` is one recovered `comp_req` need, `comp_req__csv_export_bundle`, whose body
bundles two behaviors as two separate `shall` sentences: validating the configured column headers
against the target schema, and writing one CSV row per exported need. The need carries a single
up-link, `satisfies: ["FEAT_csv_export"]`, to its parent feature, and `status: "recovered"` --
the status a synthesized need now carries coming out of `pharaoh-rev-cluster-synthesize` (see
that skill's `status` input) once `pharaoh-rev-atomicity-split` is invoked on it downstream.

This is the over-consolidation case the reverse-recovery spike measured (needs bundling more than
one atomic requirement): the atomicity rule this skill applies -- more than one `shall` in the
body -- flags it as bundled, so it is split rather than left untouched.

Expected: two atomic `comp_req` needs, `comp_req__csv_export_bundle_01` (header validation) and
`comp_req__csv_export_bundle_02` (row writing), each with exactly one `shall` clause. Both atoms
carry `satisfies: ["FEAT_csv_export"]` unchanged from the original -- the up-link is preserved on
each atom, never inverted, and neither atom links to the other or to the retired original id.
Both atoms carry `status: "recovered"`, copied verbatim from the original -- splitting never
downgrades a recovered need's status back to `draft`. Both atoms carry
`split_from: "comp_req__csv_export_bundle"` so a caller can trace them back to the need they
replace.

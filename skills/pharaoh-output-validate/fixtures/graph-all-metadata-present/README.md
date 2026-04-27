# graph-all-metadata-present

Canonical happy path for graph mode. The catalog declares `required_metadata_fields` for both `feat` and `comp_req`; every need in the corpus carries every declared field with a non-empty value.

Expected: `valid: true`, empty `violations`, `needs_checked` equals the total number of needs in the corpus.

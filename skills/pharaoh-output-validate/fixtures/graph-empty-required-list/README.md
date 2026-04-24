# graph-empty-required-list

The catalog declares `required_metadata_fields: []` for `tc` (explicitly no metadata check) and omits the key entirely for `feat` (treated as empty, also no check). Every `tc` and `feat` need in the corpus has no metadata fields. Graph mode must pass: an empty required-list — whether explicit or implicit — means "nothing to check for this type".

Expected: `valid: true`, empty `violations`, `needs_checked` equals the total number of needs.

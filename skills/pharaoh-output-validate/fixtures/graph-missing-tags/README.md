# graph-missing-tags

The catalog declares `tags` required on `comp_req`; two of the three `comp_req` needs ship without `tags` (one omits the field entirely, the other declares it as an empty list). The third `comp_req` has `tags` populated. The `feat` need has no `required_metadata_fields` declared, so it is counted but contributes no violation.

Expected: `valid: false`, `violations` sorted by `need_id` listing the two offenders with `missing_fields: ["tags"]`, `needs_checked: 4`.

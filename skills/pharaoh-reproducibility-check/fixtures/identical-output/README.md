# identical-output

Canonical happy path. Baseline and rerun each contain one `needs.json` plus one small RST file. The only difference between the two directories is the `created_at` timestamp on each need — a mask rule targeting `needs.*.created_at` with a datetime regex masks both to `"<masked>"` before diffing. After masking the two trees are byte-identical, so `overall: "pass"` and `drifted_files` is empty.

Exercises:
- the in-memory masking path on JSON files
- the wildcard segment in a dotted field path (`needs.*.created_at`)
- the vacuous-pass condition when every parseable leaf matches after masking

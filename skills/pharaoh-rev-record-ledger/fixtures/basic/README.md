# basic

Continues the CSV-export fixture used across the `rev-*` family
(`pharaoh-rev-cluster-synthesize` and `pharaoh-rev-atomicity-split`
fixtures). `input-result.json` is exactly the recovery emission this
skill consumes at the end of a synthesis rung: `reqs` is
`pharaoh-rev-cluster-synthesize`'s own `fixtures/basic/expected-output.json`
`reqs` array (one synthesized `feat` need, `FEAT_csv_export`, already
passed through `pharaoh-rev-atomicity-split` unchanged since its body is
already atomic), plus that same fixture's `member_uplinks` -- the
up-links its three pre-existing `comp_req` members
(`CREQ_csv_validate_headers`, `CREQ_csv_map_columns`,
`CREQ_csv_write_rows`) must be given so each cites the new `feat` via
`satisfies`. `source_span_lines` is `null` because a synthesized need has
no single source line to anchor (see `pharaoh-req-codelink-annotate`
running only at extraction rungs in
`pharaoh-write-plan/templates/reverse-recover-rung.yaml.j2`).

Applying `input-result.json` per this skill's Process:

- Step 2 resolves the three members via Tier 1 (`ubc build needs --format
  json`) and stages an update entry per member with `satisfies` extended
  to include `FEAT_csv_export` (each member had no prior `satisfies`
  value in this scenario, so the extended value is `["FEAT_csv_export"]`
  on each).
- Step 3 builds `needs[]`: one entry for `FEAT_csv_export` (`id`, `type`,
  `body`, plus `title`, `intent_refs`, `intent_gap`, `cluster_id` passed
  through), followed by the three member-update entries from Step 2.
- Step 4 wraps the result: `{source_path, target_rst, run, needs}`.
- Steps 5-6 write that object to a temp file and run `ubc agent reverse
  record --input <tempfile>` from `project_root`.

`expected-output.json` is the mocked CLI stdout this skill returns
verbatim from Step 7 -- one `feat` written, three `comp_req` members
updated. The exact response envelope is owned by Task 10's engine, not
by Pharaoh. This fixture records Pharaoh's current best understanding of
that shape as a documentation aid, not a guarantee the engine will match
it byte-for-byte. A full end-to-end scorer against the real `ubc agent
reverse record` binary runs once the engine ships -- out of scope for
this worktree.

# basic

Continues the CSV-export fixture used across the `rev-*` family
(`pharaoh-rev-cluster-synthesize` and `pharaoh-rev-atomicity-split`
fixtures). `input-result.json` is exactly the recovery emission this
skill consumes at the end of a synthesis rung: `reqs` is
`pharaoh-rev-cluster-synthesize`'s own `fixtures/basic/expected-output.json`
`reqs` array (one synthesized `feat` need, `FEAT_csv_export`, already
passed through `pharaoh-rev-atomicity-split` unchanged since its body is
already atomic). `source_spans` is `null` because a synthesized need has
no single source line to anchor (see `pharaoh-req-codelink-annotate`
running only at extraction rungs in
`pharaoh-write-plan/templates/reverse-recover-rung.yaml.j2`).

This skill never sees the cluster's three pre-existing `comp_req` members
(`CREQ_csv_validate_headers`, `CREQ_csv_map_columns`,
`CREQ_csv_write_rows`). Their up-link to `FEAT_csv_export` is authored
directly into RST by `pharaoh-rev-cluster-synthesize` itself, in that
skill's own `member_updates` output (see its
`fixtures/basic/expected-output.json`) -- persisted by the plan the same
way any other skill-emitted `raw_rst` is, not applied by `record`. `record`
is ledger-only and never edits RST or links, so this skill's job here is
narrower than the earlier design this fixture used to document: it wraps
and records `FEAT_csv_export` alone.

Applying `input-result.json` per this skill's Process:

- Step 2 builds `needs[]`: one entry for `FEAT_csv_export` (`id`, `type`,
  `body`, plus `title`, `intent_refs`, `intent_gap`, `cluster_id` passed
  through). `source_spans` is `null`, so no `source_span` key is added.
- Step 3 wraps the result: `{source_path, target_rst, run, needs}`.
- Steps 4-5 write that object to a temp file and run `ubc agent reverse
  record --input <tempfile>` from `project_root`.

`expected-output.json` is the mocked CLI stdout this skill returns
verbatim from Step 6 -- one `feat` written, nothing else. The exact
response envelope is owned by Task 10's engine, not by Pharaoh. This
fixture records Pharaoh's current best understanding of that shape as a
documentation aid, not a guarantee the engine will match it byte-for-byte.
A full end-to-end scorer against the real `ubc agent reverse record`
binary runs once the engine ships -- out of scope for this worktree.

See `fixtures/real-source-span` for the fixture exercising a real,
non-null `source_span` (the two-element-array shape this fixture, with
its all-`null` `source_spans`, never exercises).

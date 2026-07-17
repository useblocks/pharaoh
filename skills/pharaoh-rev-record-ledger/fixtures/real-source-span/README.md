# real-source-span

Exercises the `source_span` two-element-array shape `fixtures/basic`
never exercises (its `source_spans` is all-`null`). `input-result.json`
is an extraction-rung emission: two `comp_req` reqs from
`src/csv_export/exporter.py`, no `member_updates` involved (extraction
rungs never carry them -- only `pharaoh-rev-cluster-synthesize` at a
synthesis rung authors member up-link RST).

`source_spans` is `[[11, 18], null]`, order-aligned with `reqs`:

- `CREQ_csv_validate_headers` carries a real element range, `[11, 18]`
  -- the 0-based inclusive line range of the `validate_headers` function
  it traces to, the kind of value that would come from a real
  `CodelinkSourceMap.line_range` / `src-trace` resolution, never from
  `pharaoh-req-codelink-annotate`'s `inserted_line` (a single int marking
  where the *comment* was inserted, not the element's own range -- see
  `pharaoh-rev-record-ledger/SKILL.md` Input).
- `CREQ_csv_map_columns` carries `null` -- no element range was resolved
  for it in this scenario.

`expected-recovery-result.json` is the exact `RecoveryResult` this skill
builds and writes to the temp file (Step 3 of Process):

- `needs[0].source_span == [11, 18]` -- a two-element `[start_line,
  end_line]` array, matching the engine's `RecoveredNeed.source_span:
  Option<[u32; 2]>`. This is the shape `serde_json::from_str::<RecoveryResult>`
  actually parses. The earlier `{file, line}` object shape this fixture
  used to assert would hard-fail deserialization on the engine side.
- `needs[1]` carries no `source_span` key at all -- `null` in,
  key omitted out, so it deserializes to `None` on the Rust side rather
  than tripping on a JSON `null` where the field expects either an
  absent key or a two-element array.

`expected-output.json` is the mocked CLI stdout this skill returns
verbatim from Step 6: `{"shard_path": "...", "need_count": 2}`, the same
engine `RecordOutcome` shape `fixtures/basic` documents (see that
fixture's README for the shard-path derivation) -- `need_count` is `2`
here since this fixture's `RecoveryResult` carries both `comp_req` reqs.

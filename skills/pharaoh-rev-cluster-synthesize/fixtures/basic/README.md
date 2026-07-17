# basic

Three lower `comp_req` needs (`CREQ_csv_validate_headers`, `CREQ_csv_map_columns`, `CREQ_csv_write_rows`) already exist for a CSV Exporter component but share no upper-rung `feat` anchor. `input-cluster.json` provides the precomputed cluster (`cluster_id: cluster_csv_export`) with the three member ids and their resolved bodies, standing in for what `ubc build needs --format json` would return for those ids (Tier 1 of `shared/data-access.md`).

`input-intent.json` supplies two intent snippets: a commit message and a PR description, both naming "CSV export" explicitly. Both snippets ground the same theme the three members compose, so both qualify as `intent_refs`.

Expected: one synthesized `feat` need (`FEAT_csv_export`) whose body covers all three member behaviors (header validation, column mapping, row writing), whose `satisfies` lists exactly the three member ids, whose `intent_refs` cites both intent snippet ids, and whose `intent_gap` is `false` since the intent signal grounds the rung. This is the fixture's happy path -- a cluster with a coherent shared theme and intent signal that actually names it, as opposed to a cluster requiring an `intent_gap: true` result.

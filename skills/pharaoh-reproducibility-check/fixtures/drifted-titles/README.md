# drifted-titles

Expected-fail case. Baseline and rerun share identical ids and timestamps (no mask rule needed for the timestamp in this fixture — the values match byte-for-byte), but the rerun has paraphrased two of the three `title` fields. No mask rule targets `title`, so every title change is real drift. Expected verdict is `overall: "fail"` with one drifted file (`needs.json`) and two entries under `fields_changed` — the dotted paths to the two changed titles. The third, unchanged title does not show up.

Exercises:
- deep dict-compare on the parsed JSON
- per-field drift reporting under `drift_summary` at path-into-record granularity
- the file-level drift gate (one file drifted → `overall: "fail"`)
- no-op masking (the `mask_rules` list is present but no entry fires, so the rerun's title changes are fully visible in the diff)

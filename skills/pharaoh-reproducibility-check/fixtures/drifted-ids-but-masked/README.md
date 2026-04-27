# drifted-ids-but-masked

Expected-pass case that demonstrates the `mask_rules` escape hatch for randomly-generated fields. Baseline and rerun share the same outer need-ids (stable dict keys), but each need carries a `generated_run_id` field whose value is a hex token produced by the plan executor at runtime — the two runs produced different tokens (`a3f7c09e` vs `b18d4f22`). Without masking, every need would drift on that field and the file would fail the check. With a single mask rule targeting `needs.*.generated_run_id` and a hex-token regex, both sides are rewritten in-memory to `"<masked>"` before the diff, so the compared structures are equal.

Expected verdict: `overall: "pass"`, empty `drifted_files`.

Exercises:
- the mask-rule escape hatch: a value that really differs between runs is hidden from the diff when the caller declares it non-deterministic
- the wildcard `*` in the dotted field path
- the `re.search` semantics (the regex matches anywhere in the value; it does not need to fullmatch)

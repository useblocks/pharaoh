# some-violate

Mixed corpus exercising the failure path. Five needs across two types:

- 2 conforming (`CREQ_reqif_cli_load`, `tc__reqif_cli_load_happy_path`) — do not appear in the output.
- 2 non-conforming `comp_req` ids (`CREQ_reqif_cli` has only two segments after the prefix; `CREQ_a` is a single-segment tail).
- 1 non-conforming `test_case` id (`TC_REQIF_CLI_LOAD` uses the wrong case and separator).

Expected output: `overall: "fail"`, `needs_checked: 5`, `violations` sorted by `need_id` with three entries each naming the regex actually applied and the `"does not match"` reason. Confirms per-type resolution selects the right regex for each offender and that the output order is deterministic.

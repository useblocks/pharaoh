# all-conform

Canonical happy path. The tailoring declares a per-type regex for `comp_req` (`^CREQ_[a-z]+_[a-z]+_[a-z]+$`) and `test_case` (`^tc__[a-z0-9_]+$`), plus a sensible top-level default. Every need in `input-needs.json` matches the regex for its type, so `overall == "pass"` and `violations` is empty. Exercises the per-type resolution path and confirms `fullmatch` accepts well-formed ids.

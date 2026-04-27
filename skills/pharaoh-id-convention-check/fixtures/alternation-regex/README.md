# alternation-regex

Exercises the "two legal forms" policy the skill supports via regex alternation, not via auto-detection. The tailoring declares a single regex for `comp_req` — `^CREQ_.+$|^gd_req__.+$` — which explicitly accepts both the new `CREQ_*` prefix and the legacy `gd_req__*` prefix.

All four ids in `input-needs.json` are valid: two match the first branch, two match the second. Expected output: `overall: "pass"`, empty `violations`. This fixture confirms:

1. `re.fullmatch` is applied — both alternation branches have explicit anchors and both match.
2. The atom does not report "mixed schemes detected" — scheme policy is the tailoring author's decision, encoded in the regex value. The atom only applies the regex.

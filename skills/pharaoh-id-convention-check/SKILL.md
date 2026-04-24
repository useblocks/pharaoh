---
name: pharaoh-id-convention-check
description: Use when verifying that every need id in a sphinx-needs corpus matches the regex declared for its type in `.pharaoh/project/id-conventions.yaml`. Single mechanical structural check — applies the tailored per-type regex, emits a list of violations. Does NOT auto-detect how many schemes coexist — scheme policy is the tailoring author's responsibility (declare an alternation to allow multiple forms).
---

# pharaoh-id-convention-check

## When to use

Invoke from `pharaoh-quality-gate.required_checks` (invariant: `id-convention-consistent`) or directly after a build to confirm the corpus obeys its declared id scheme. Reads `id-conventions.yaml` + `needs.json`, returns findings JSON listing every need whose `id` does not match the regex for its `type`.

Do NOT use to discover or count id schemes — the tailoring author declares ONE canonical regex per type and this atom only reports violations against that regex. If multiple forms are legal (e.g. legacy plus new prefix), the tailoring author encodes that as an alternation in the regex (`^CREQ_.+$|^gd_req__.+$`). Do NOT use to rename ids or mutate the corpus — read-only.

## Atomicity

- (a) Indivisible: one `id-conventions.yaml` + one `needs.json` in → one findings JSON out. No scheme counting, no regex inference, no id rewriting, no dispatch of other skills.
- (b) Input: `{id_conventions_path: str, needs_json_path: str}`. Output: JSON `{needs_checked: int, violations: [{need_id, type, expected_regex, reason}], overall: "pass" | "fail"}`.
- (c) Reward: fixtures under `skills/pharaoh-id-convention-check/fixtures/` — one per outcome:
  1. `all-conform/` — every id matches its type's regex → matches `expected-output.json` (`overall: "pass"`, empty `violations`, `needs_checked == len(needs)`).
  2. `some-violate/` — mix of conforming and non-conforming ids across two types → `overall: "fail"`, `violations` lists each offender with its `type`, the `expected_regex` applied, and a short `reason`.
  3. `alternation-regex/` — tailoring declares `^CREQ_.+$|^gd_req__.+$` and both forms are used in the corpus → `overall: "pass"` because the alternation matches both.

  Pass = all 3 fixture outputs match `expected-output.json` exactly (modulo ordering of `violations`, which is sorted by `need_id` in the emitted output).
- (d) Reusable across projects — the regex is data-driven via tailoring; no project-specific prefix or separator is hardcoded. Works for any sphinx-needs corpus with an `id-conventions.yaml`.
- (e) Read-only. No side effects. Does not modify the tailoring file or the needs corpus. Running twice on identical inputs yields byte-identical output.

## Input

- `id_conventions_path`: absolute path to the tailoring file `.pharaoh/project/id-conventions.yaml`. Schema accepted:

  ```yaml
  # top-level default regex applied to any type without an override
  id_regex: "^[a-z][a-z_]*__[a-z0-9_]+$"

  # per-type overrides — the regex applied to needs of that type
  id_regex_by_type:
    comp_req: "^CREQ_[a-z]+_[a-z]+_[a-z]+$"
    gd_req:   "^CREQ_.+$|^gd_req__.+$"
  ```

  Resolution order for a need of type `T`: `id_regex_by_type[T]` if declared, else `id_regex` (top-level default), else fail the whole check with `reason: "no regex declared for type <T>"` on every need of that type.

- `needs_json_path`: absolute path to the built sphinx-needs corpus `needs.json`. Accepts either the flat `{"needs": {<id>: {id, type, ...}, ...}}` shape or the versioned `{"versions": {"<v>": {"needs": {...}}}}` shape (uses `current_version` if declared, else the latest key). Each need object must carry at least `id` and `type`; needs missing either field are reported as violations with `reason: "missing id or type field"`.

Edge cases:
- Empty corpus (`needs` is `{}`) → `needs_checked: 0, violations: [], overall: "pass"` (vacuously true).
- `id-conventions.yaml` has neither `id_regex` nor `id_regex_by_type` → every need is a violation with `reason: "no regex declared for type <T>"`.
- Regex compilation error (invalid Python regex syntax in the tailoring) → `overall: "fail"` with a single violation `{need_id: "*", type: "<T>", expected_regex: "<bad regex>", reason: "regex compile error: <python error>"}` and `needs_checked: 0`.
- Need `type` not mentioned in `id_regex_by_type` and no top-level default → violation with `reason: "no regex declared for type <T>"`.

## Output

```json
{
  "needs_checked": 44,
  "violations": [
    {
      "need_id": "comp_req__login_ok",
      "type": "comp_req",
      "expected_regex": "^CREQ_[a-z]+_[a-z]+_[a-z]+$",
      "reason": "does not match"
    },
    {
      "need_id": "CREQ_a",
      "type": "comp_req",
      "expected_regex": "^CREQ_[a-z]+_[a-z]+_[a-z]+$",
      "reason": "does not match"
    }
  ],
  "overall": "fail"
}
```

`overall` is `"pass"` iff `violations` is empty. `needs_checked` counts every need that was read from `needs.json` (including ones that triggered a "no regex declared" violation — they are still counted). `violations` is sorted by `need_id` ascending for deterministic fixture comparison. `reason` is a short human string: one of `"does not match"`, `"missing id or type field"`, `"no regex declared for type <T>"`, or `"regex compile error: <python error>"`.

## Detection rule

For every need `N` in the flattened needs map:

1. Read `N.id` and `N.type`. If either is absent, emit violation `{need_id: <whatever id is, or "<missing>">, type: <or "<missing>">, expected_regex: null, reason: "missing id or type field"}` and continue.
2. Resolve the regex for `N.type`: first `id_regex_by_type[N.type]`, else top-level `id_regex`. If neither is declared, emit violation `{need_id: N.id, type: N.type, expected_regex: null, reason: "no regex declared for type <N.type>"}` and continue.
3. Compile the regex with Python `re.compile(pattern)`. On `re.error`, emit a single synthetic violation (see Edge cases above) and abort.
4. Apply `re.fullmatch(pattern, N.id)`. If `None`, emit violation `{need_id: N.id, type: N.type, expected_regex: <pattern>, reason: "does not match"}`.

`fullmatch` (not `search` or `match`) is load-bearing: the regex describes the entire id, anchors or not. This rule is what lets the tailoring author write `^CREQ_.+$|^gd_req__.+$` and have both forms pass without the alternation implicitly anchoring only the first branch.

Minimum viable Python reference implementation (≤ 30 lines):

```python
import json, re, yaml, sys

conv  = yaml.safe_load(open(id_conventions_path))
nj    = json.load(open(needs_json_path))
needs = nj.get("needs") or next(iter(nj.get("versions", {}).values()), {}).get("needs", {})

default = conv.get("id_regex")
by_type = conv.get("id_regex_by_type", {}) or {}

violations = []
for nid, n in needs.items():
    t = n.get("type"); i = n.get("id", nid)
    if not t or not i:
        violations.append({"need_id": i or "<missing>", "type": t or "<missing>",
                           "expected_regex": None, "reason": "missing id or type field"}); continue
    pat = by_type.get(t, default)
    if pat is None:
        violations.append({"need_id": i, "type": t, "expected_regex": None,
                           "reason": f"no regex declared for type {t}"}); continue
    try:
        rx = re.compile(pat)
    except re.error as e:
        print(json.dumps({"needs_checked": 0, "violations": [
            {"need_id": "*", "type": t, "expected_regex": pat,
             "reason": f"regex compile error: {e}"}], "overall": "fail"})); sys.exit(0)
    if not rx.fullmatch(i):
        violations.append({"need_id": i, "type": t, "expected_regex": pat, "reason": "does not match"})

violations.sort(key=lambda v: v["need_id"])
print(json.dumps({"needs_checked": len(needs),
                  "violations": violations,
                  "overall": "pass" if not violations else "fail"}))
```

## Failure modes

- **Scheme auto-detection is explicitly out of scope.** This atom does NOT answer "how many id schemes exist in this corpus?" — that is a tailoring-authoring concern, served by `pharaoh-tailor-detect`. If a project wants to allow two prefixes, the tailoring author writes an alternation regex; this check applies whatever regex is declared.
- **No Unicode normalisation.** Ids are matched byte-for-byte against the regex. Non-ASCII ids work only if the regex accounts for them. Sphinx-needs ids are ASCII in practice, so this is not a blocker.
- **No type-name validation against `artefact-catalog.yaml`.** An id of type `T` whose `T` is absent from the artefact catalog will still be checked against the default regex (or flagged with "no regex declared"). Cross-file consistency of type names is `pharaoh-tailor-review`'s job, not this atom's.
- **`fullmatch` semantics.** Writers of the tailoring must know their regex will be `fullmatch`-ed. Adding redundant anchors (`^...$`) is harmless; omitting anchors also works. Using `re.search`-style partial patterns that were intended to match substrings will misbehave — document this in project tailoring.

## Composition

Role: `atom-check`.

Called by `pharaoh-quality-gate` when `required_checks` contains `id_convention_consistent: true`, under the invariant delegation entry `id-convention-consistent`. Never invokes other skills; never dispatched from emission skills. May also be invoked directly by a human auditor inspecting a corpus.

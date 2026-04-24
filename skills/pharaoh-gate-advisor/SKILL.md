---
name: pharaoh-gate-advisor
description: Use when reading a project's `pharaoh.toml` to report which phased-enablement ladder step is the recommended next gate to switch on. Single mechanical advisory check — parses five flags (`strictness`, `require_verification`, `require_change_analysis`, `require_mece_on_release`, `codelinks.enabled`), walks the fixed ladder in order, and emits the first unmet step plus its blocker note. Read-only; never edits `pharaoh.toml`.
---

# pharaoh-gate-advisor

## When to use

Invoke after `pharaoh-bootstrap` + `pharaoh-setup` have landed a `pharaoh.toml`, whenever an auditor asks "which gate should we switch on next?", or as a recurring prompt in a project-health review. Reads `pharaoh.toml`, reports the current state of the five ladder knobs, and names the FIRST ladder step whose flag is not yet enabled along with the pre-work that blocks enabling it. When every step is satisfied, returns `recommended_next_gate: null` with `rationale: "ladder complete"`.

The ladder is fixed and ordered by value / cost ratio — cheapest-and-most-effective first, hardest-and-most-disruptive last. Advancing one step at a time makes the transition from "advisory everywhere" to "enforcing everywhere" debuggable — a project that flips `strictness = "enforcing"` before any individual gate is on ships a gate that enforces nothing, then gets blamed when a later flip fails.

Do NOT invoke to modify `pharaoh.toml` — this skill is advisory, read-only. Auto-enablement belongs in `pharaoh-setup` or a future `pharaoh-setup-reconfigure`, not here. Do NOT invoke to grade the QUALITY of the gates' effects (whether review coverage is good, whether MECE is clean) — that is `pharaoh-quality-gate`. Do NOT invoke to reason about gates not in the ladder (e.g. `[pharaoh.traceability]`); the ladder is deliberately five steps.

## Atomicity

- (a) Indivisible: one `pharaoh.toml` in → one findings JSON out. No file writes, no dispatch of other skills, no reasoning about anything besides the five ladder flags.
- (b) Input: `{pharaoh_toml_path: str}`. Output: findings JSON per the shape in `## Output` below.
- (c) Reward: fixtures under `skills/pharaoh-gate-advisor/fixtures/` — one per ladder outcome:
  1. `fresh-from-bootstrap/` — every flag at its advisory default (`strictness = "advisory"`, all four booleans `false`). Expected: `recommended_next_gate == "require_verification"`, rationale names step 1 as the lowest-cost enablement, `ladder[0].blocker == "none — safe to enable now"`.
  2. `step-1-enabled/` — `require_verification = true`, the remaining three booleans `false`, strictness advisory. Expected: `recommended_next_gate == "require_change_analysis"`, rationale names step 2 and the pharaoh-change tailoring blocker.
  3. `all-steps-enabled/` — `strictness = "enforcing"`, all four booleans `true`. Expected: `recommended_next_gate == null`, rationale `"ladder complete"`, every ladder entry reports its flag as enabled.

  Pass = each fixture's actual output matches `expected-output.json` byte-for-byte (the ladder array is fixed and deterministic).
- (d) Reusable across projects — the ladder ships with zero project-specific vocabulary. Only `pharaoh.toml`'s own key names appear, and those are the same for every Pharaoh consumer. Tailoring extension point: projects may override `rationale` text via `tailoring.gate_advisor_rationale_overrides` if they want house-style blocker notes, but the ladder ORDER is fixed.
- (e) Read-only. Does not modify `pharaoh.toml`, `pharaoh.toml.example`, or any on-disk state. Running twice on identical input yields byte-identical output.

## Input

- `pharaoh_toml_path`: absolute path to the project's `pharaoh.toml`. The skill reads exactly five keys:
  - `[pharaoh].strictness` — string; treated as `"advisory"` unless the value is exactly `"enforcing"`.
  - `[pharaoh.workflow].require_verification` — boolean; default `false` when absent.
  - `[pharaoh.workflow].require_change_analysis` — boolean; default `false` when absent.
  - `[pharaoh.workflow].require_mece_on_release` — boolean; default `false` when absent.
  - `[pharaoh.codelinks].enabled` — boolean; default `false` when absent.

Edge cases:
- `pharaoh_toml_path` missing or unreadable → emit `overall: "error"` with `errors: ["pharaoh.toml unresolved: <path>"]` and no other keys. Callers branch on `overall` first. No ladder array is emitted on this path — the ladder is meaningful only when the file parsed.
- TOML parse error (syntax bad) → same `overall: "error"` shape with the parser message included.
- Keys present but with unexpected types (e.g. `require_verification = "yes"` as a string) → treat as their typed default (`false` for booleans, `"advisory"` for strictness) and add a note `"unexpected type for <key>; treated as default"` in `notes`.
- Entire `[pharaoh.workflow]` or `[pharaoh.codelinks]` section absent → every flag in that section resolves to its `false` default; no error.

## Output

```json
{
  "current_state": {
    "strictness": "advisory",
    "require_verification": false,
    "require_change_analysis": false,
    "require_mece_on_release": false,
    "codelinks_enabled": false
  },
  "recommended_next_gate": "require_verification",
  "rationale": "require_verification = true is the highest-value, lowest-cost step — it wires the review skills that are already ship-ready into the release gate and catches every PARTIAL finding via pharaoh-req-review. No pre-work required.",
  "ladder": [
    {"step": 1, "gate": "require_verification = true",     "blocker": "none — safe to enable now"},
    {"step": 2, "gate": "require_change_analysis = true",  "blocker": "needs pharaoh-change to be tailored"},
    {"step": 3, "gate": "require_mece_on_release = true",  "blocker": "needs release-gate workflow"},
    {"step": 4, "gate": "codelinks.enabled = true",        "blocker": "needs codelink annotations in source"},
    {"step": 5, "gate": "strictness = enforcing",          "blocker": "requires steps 1-4 satisfied"}
  ],
  "overall": "pass",
  "notes": []
}
```

Fields (in canonical order):
- `current_state`: echo of the five parsed flags, using the canonical key names above. `codelinks_enabled` is underscored here even though the TOML key is `codelinks.enabled`, so the JSON is flat and one-shape.
- `recommended_next_gate`: the canonical key name of the FIRST ladder step whose corresponding config field is not yet at its enabled value. One of `"require_verification"`, `"require_change_analysis"`, `"require_mece_on_release"`, `"codelinks_enabled"`, `"strictness_enforcing"`, or `null` when the ladder is complete.
- `rationale`: one or two sentences naming why this step is the next one — what it unlocks and what (if anything) blocks enabling it right now. On `null` recommendation, the string is exactly `"ladder complete"`.
- `ladder`: the fixed five-entry array shown above, shipped verbatim in every non-error response. Each entry has `step` (1–5), `gate` (the TOML-style line the project would add), and `blocker` (the pre-work the project must complete first, or `"none — safe to enable now"` for step 1).
- `overall`: `"pass"` when the file parsed and the ladder computed. `"error"` when the file failed to resolve or parse (see Edge cases).
- `notes`: any non-fatal observations (e.g. mistyped value, absent section treated as default). Empty list when clean.

## Detection rule

Two passes over the input; both mechanical, no LLM judgement.

### 1. Parse the five flags

**Check:** Load `pharaoh.toml` as TOML. Read each of the five keys per the `## Input` section. Apply defaults for missing keys. Coerce unexpected types to their defaults and add a note.

**Detection:**
```python
import tomllib

with open(pharaoh_toml_path, "rb") as fh:
    data = tomllib.load(fh)

strictness = data.get("pharaoh", {}).get("strictness", "advisory")
if strictness != "enforcing":
    strictness = "advisory"

wf = data.get("pharaoh", {}).get("workflow", {})
rv = wf.get("require_verification", False) is True
rca = wf.get("require_change_analysis", False) is True
rmr = wf.get("require_mece_on_release", False) is True

cl = data.get("pharaoh", {}).get("codelinks", {})
ce = cl.get("enabled", False) is True
```

### 2. Walk the fixed ladder

**Check:** Iterate the five ladder entries in order. The first entry whose corresponding flag is NOT at its enabled value is the `recommended_next_gate`. If all five are at their enabled value, `recommended_next_gate` is `null`.

Enabled values per step (canonical):
1. `require_verification` enabled iff `rv is True`.
2. `require_change_analysis` enabled iff `rca is True`.
3. `require_mece_on_release` enabled iff `rmr is True`.
4. `codelinks_enabled` enabled iff `ce is True`.
5. `strictness_enforcing` enabled iff `strictness == "enforcing"`.

**Detection:**
```python
LADDER = [
    ("require_verification",   rv,                            "none — safe to enable now"),
    ("require_change_analysis", rca,                          "needs pharaoh-change to be tailored"),
    ("require_mece_on_release", rmr,                          "needs release-gate workflow"),
    ("codelinks_enabled",       ce,                           "needs codelink annotations in source"),
    ("strictness_enforcing",    strictness == "enforcing",    "requires steps 1-4 satisfied"),
]

recommended = next((name for name, enabled, _ in LADDER if not enabled), None)
```

The ladder array in the output is derived once from a static template (see `## Output`); only `recommended_next_gate`, `rationale`, and `current_state` vary per input. `overall` is `"pass"` on any successful parse.

`rationale` text is drawn from a static map keyed by `recommended_next_gate`:

| `recommended_next_gate`      | Default rationale                                                                                                                              |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `require_verification`       | "require_verification = true is the highest-value, lowest-cost step — it wires the review skills that are already ship-ready into the release gate and catches every PARTIAL finding via pharaoh-req-review. No pre-work required." |
| `require_change_analysis`    | "require_change_analysis = true is the next step. Blocker: pharaoh-change must be tailored for this project before the gate is meaningful — otherwise every authoring task will trip an alarm with no mitigation path." |
| `require_mece_on_release`    | "require_mece_on_release = true is the next step. Blocker: the project needs a release-gate workflow that understands how to invoke pharaoh-mece and act on its findings." |
| `codelinks_enabled`          | "codelinks.enabled = true is the next step. Blocker: the source tree needs codelink annotations (`@req`, `@impl`, etc.) on the symbols this project wants to trace, otherwise the flag activates an empty traceability view." |
| `strictness_enforcing`       | "strictness = enforcing is the final step. Blocker: steps 1-4 must all be satisfied first — flipping strictness before the individual gates are on ships a gate that enforces nothing." |
| `null`                       | "ladder complete"                                                                                                                              |

Projects override any row via `tailoring.gate_advisor_rationale_overrides[<key>]` in `.pharaoh/project/checklists/gate-advisor.md` (optional). The ladder ORDER and the `gate` / `blocker` strings are fixed and not overridable.

## Tailoring extension point

- `tailoring.gate_advisor_rationale_overrides`: map of `{recommended_next_gate: rationale_string}` that replaces the default rationale when emitted. A project that prefers short blocker notes, or that wants to surface internal-ticket links in the rationale, uses this. The key set must match the canonical `recommended_next_gate` names above; unknown keys are ignored with a `notes` entry.

No other knobs are exposed. The ladder itself is the shared reference `skills/shared/gate-enablement.md` — a project that disagrees with the ladder order should file an issue against the shared reference, not fork this atom.

## Composition

Role: `atom-check`.

Called standalone by auditors, by `pharaoh-process-audit` as an optional health check, or from a CI job that wants a deterministic recommendation in the project dashboard. Never invoked by `pharaoh-quality-gate` (this atom is advisory, not a gate invariant — the gate invariants check the effects of the flags, not whether the flags themselves are set). Never dispatches other skills. Never modifies `pharaoh.toml`.

Related but distinct:
- `pharaoh-setup` ships step 1 (`require_verification = true`) on by default — so a fresh project running this skill straight after setup lands on step 2 as the recommendation.
- `shared/gate-enablement.md` documents the rationale for the ladder order; projects read it to understand WHY each step is where it is.
- `pharaoh-quality-gate` runs the invariants that the ladder flags control — it answers "are my gates passing?", not "which gate should I enable next?".

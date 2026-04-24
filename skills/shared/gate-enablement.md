# Gate enablement ladder

Shared reference documenting the fixed five-step ladder that Pharaoh projects walk to move from "advisory everywhere" to "enforcing everywhere". Consumed by `pharaoh-gate-advisor` (which walks it mechanically and reports the next unmet step) and by `pharaoh-setup` / `pharaoh-bootstrap` (which ship step 1 enabled by default). Treated as documentation, not a skill.

## The rule

The ladder is fixed, ordered, and five steps. Projects advance one step at a time. Advancing more than one step per change makes failure-to-enable debugging ambiguous — if two flips land together and the build alarms, the project cannot cheaply tell which flip is to blame.

| Step | Gate (TOML line)                 | Blocker (pre-work required)                        | Rationale                                                                                                    |
|------|----------------------------------|----------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 1    | `require_verification = true`    | none — safe to enable now                           | Review skills (`pharaoh-req-review`, `pharaoh-arch-review`, etc.) are ship-ready and read-only. Enabling this catches every PARTIAL finding immediately at no implementation cost. Highest value, lowest cost. |
| 2    | `require_change_analysis = true` | `pharaoh-change` must be tailored for this project | The change-analysis skill needs the project's impact model (which needs touch which code, which tests cover which reqs). Flipping the flag before the model exists alarms every authoring task with no mitigation path. |
| 3    | `require_mece_on_release = true` | release-gate workflow exists                        | MECE checks run at release time, not mid-authoring. The flag is meaningful only when there's a release pipeline that actually invokes `pharaoh-quality-gate` and acts on its `pass`/`fail` verdict. |
| 4    | `codelinks.enabled = true`       | source tree has codelink annotations                | Enabling the flag activates a traceability view that grows as source gets annotated. On an unannotated source tree the view is empty; the flag does no harm, but it also signals nothing useful until annotations land. |
| 5    | `strictness = "enforcing"`       | steps 1–4 all satisfied                             | The master flag. Flipping strictness to `enforcing` before the individual gates are on ships a gate that enforces nothing — then later flips of the individual gates cause surprise blocks because strictness was the only part already hot. |

## Why this order

The common alternative — "turn strictness enforcing first, then enable individual gates" — is what produced a dogfooding failure pattern. When strictness flipped to enforcing on day one, the individual gate flags were all `false`, so enforcing had zero teeth. Later, flipping one gate such as `require_change_analysis = true` immediately blocked every authoring task, because the other half of the gate (strictness) had been enforcing the whole time, just silently.

Walking the ladder in value-cost order avoids that surprise:
- Step 1 has no cost and immediate value → enable immediately.
- Steps 2–4 each require concrete pre-work whose absence is easy to check (did you tailor `pharaoh-change`? do your releases invoke MECE? is your source annotated?). A project that CAN enable the step should; a project that CANNOT should ship the pre-work first.
- Step 5 is a synthesis step. Its enabling condition is "all four previous flags are already `true`". Flipping it is low risk at that point because every gate it governs has already been exercised independently.

## Bootstrap defaults

`pharaoh-setup` ships `require_verification = true` out of the box — step 1 of the ladder enabled by default. A fresh project that runs setup and then `pharaoh-gate-advisor` immediately receives step 2 as its next recommendation, not step 1. This is a deliberate reversal of the pre-2026-04-22 default where every gate shipped `false`; a shipped-as-advisory-everywhere config teaches the user that gates are optional cosmetic knobs, which is not the signal Pharaoh wants to send.

All other flags still ship at their advisory defaults (`false` / `"advisory"`) because each one has pre-work that projects must clear before enabling is meaningful. Step 1 is the only step with no pre-work, so it is the only step safe to ship hot.

## Per-mode interaction

`pharaoh-setup` also classifies the project into `reverse-eng` / `greenfield` / `steady-state` modes (see `pharaoh-setup` Step 2a.bis). The mode table sets the three workflow flags' initial values. After 2026-04-22 the table looks like:

| Mode           | `require_change_analysis` | `require_verification` | `require_mece_on_release` |
|----------------|---------------------------|------------------------|---------------------------|
| `reverse-eng`  | `false`                   | `true`                 | `false`                   |
| `greenfield`   | `false`                   | `true`                 | `false`                   |
| `steady-state` | `true`                    | `true`                 | `true`                    |

`require_verification = true` is now uniform across all three modes — the ladder says step 1 is safe everywhere, and the mode-specific defaults defer to that. Mode still differentiates the other two flags (reverse-eng and greenfield keep change-analysis and MECE off until the catalogue stabilises).

## What this reference is NOT

- NOT a gate itself. `pharaoh-quality-gate` runs invariants against the effects of the flags (review coverage, draft-lifecycle, id-convention, etc.). The ladder talks about WHICH FLAGS to turn on, not whether those flags' effects are passing.
- NOT a substitute for `pharaoh.toml`'s own documentation. Each key is documented in `pharaoh.toml.example` and `skills/shared/strictness.md`. This reference layers phasing on top of that documentation; read both.
- NOT a tailoring extension point. Projects do not fork the ladder; they ship rationale overrides via `tailoring.gate_advisor_rationale_overrides` if they want house-style blocker notes, but the ladder ORDER is fixed. If your project disagrees with the order, file an issue against this reference — forking it per-project silently defeats the shared-meaning-across-projects signal that the ladder is trying to carry.

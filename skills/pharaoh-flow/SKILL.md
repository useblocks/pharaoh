---
name: pharaoh-flow
description: "Use when orchestrating the full V-model chain for one feature context — across the optional ISO 26262 safety V (hazard / safety_goal / fsr), the ASPICE SYS layer (sysreq / sys-arch), the ASPICE SW layer (swreq / swarch), and the classical component V (req / comp_req → arch → vplan → fmea), each with a review pass. Auto-detects which layers to run from `.pharaoh/project/artefact-catalog.yaml`; the caller can pass a `stages` argument to skip layers explicitly. Dispatches to pharaoh-req-draft, pharaoh-req-review, pharaoh-arch-draft, pharaoh-arch-review, pharaoh-vplan-draft, pharaoh-vplan-review, and pharaoh-fmea — no new safety-V drafting skills are introduced; safety-V types route through pharaoh-req-draft with the appropriate target_level."
chains_from: []
chains_to: []
---

# pharaoh-flow

## When to use

Invoke when the user wants to produce a complete V-model artefact chain from a single feature
context in one operation. This skill orchestrates the atomic drafting and review skills; it
does not author content itself.

**Scope is bounded to one feature context.** Each layer that runs emits exactly one artefact
of each type the layer covers, with a review pass after every drafted artefact.

The orchestrator walks up to three optional layers, top-down through the V:

| Layer | Stages drafted | Catalog types it expects |
|---|---|---|
| `safety_v` | hazard → safety_goal → fsr | `hazard`, `safety_goal`, `fsr` |
| `sys` | sysreq → sys-arch | `sysreq`, `sys-arch` |
| `sw` | swreq → swarch | `swreq`, `swarch` |
| `component` | req (or `comp_req` / `gd_req`) → arch → vplan → fmea | one requirement-shaped key (e.g. `req`, `comp_req`, `gd_req`), `arch`, `tc`, `fmea` |

A layer runs only if its types are declared in `.pharaoh/project/artefact-catalog.yaml`. A
project that declares only the classical types runs only the `component` layer (the prior
behaviour of this skill is preserved exactly).

Do NOT invoke when the user wants to draft only one artefact type — use the individual atomic
skills directly. Do NOT invoke when the feature context implies multiple requirements at the
same level (the orchestrator drafts the single most direct requirement per layer and advises
re-invocation).

> This is a compositional orchestrator. The atomicity criterion (a) does not apply: by design
> it invokes multiple skills. Scope is bounded to "one feature → one V-model chain across the
> declared layers".

---

## Inputs

- **feature_context** (from user): short prose describing the feature / hazard / safety goal
  (1–5 sentences). Forwarded to the top-most layer that runs.
- **parent_link** (from user): need-id of the parent the top-most layer's first artefact will
  trace to (e.g. a workflow id for safety-V, an upstream sysreq id when entering at SYS, etc.).
  When a higher layer runs first, the lower layers chain off the IDs produced upstream — the
  caller does not supply an extra parent for each layer.
- **safety_context** (from user, optional): ASIL level (A–D) or safety-goal handle if known —
  forwarded to `pharaoh-req-draft` (for safety-V types) and to `pharaoh-fmea`.
- **stages** (from user, optional): explicit list of layers to run. Allowed values:
  `safety_v`, `sys`, `sw`, `component`. Order in the input is ignored — the orchestrator always
  walks the layers top-down (`safety_v` → `sys` → `sw` → `component`). When omitted,
  auto-detect from the catalog.
- **tailoring** (from `.pharaoh/project/`): every sub-skill consumes `artefact-catalog.yaml`,
  `id-conventions.yaml`, `workflows.yaml`, and per-type checklists.
- **needs.json**: required for parent resolution and uniqueness checks in each sub-skill.

### Auto-detect vs. explicit `stages`

Default behaviour is **auto-detect**: the orchestrator runs every layer whose types are
declared in the catalog. This is the correct mode for a project that has finished tailoring
and wants the full V emitted in one call.

The caller passes `stages` explicitly when:

- A project is **bootstrapping** the safety V and wants only the upper-V emitted while the
  classical layer is still being shaped. Without an explicit `stages: ["safety_v"]`,
  auto-detect would also try to run the lower layers.
- An audit run wants to **regenerate one layer in isolation** without retouching others
  already emitted (e.g. `stages: ["sys"]` to refresh the SYS layer after a tailoring edit).
- The catalog declares a layer's types but the caller knows that layer's parent IDs aren't
  yet stable, so the layer should be deferred.

When `stages` is supplied, every requested layer must have its types declared in the catalog;
a missing declaration is a hard FAIL (see Guardrail G2).

---

## Outputs

For every layer that runs, emit each drafted artefact and its review (where the layer
includes one) in a labeled fenced block, then a single flow summary at the end. Block
ordering follows the V (top-down then layer-internal):

```
=== [SAFETY_V 1/3] hazard: <id> ===              (only if layer ran)
=== [REVIEW SAFETY_V 1/3] req-review: <id> ===
=== [SAFETY_V 2/3] safety_goal: <id> ===
=== [REVIEW SAFETY_V 2/3] req-review: <id> ===
=== [SAFETY_V 3/3] fsr: <id> ===
=== [REVIEW SAFETY_V 3/3] req-review: <id> ===

=== [SYS 1/2] sysreq: <id> ===                   (only if layer ran)
=== [REVIEW SYS 1/2] req-review: <id> ===
=== [SYS 2/2] sys-arch: <id> ===
=== [REVIEW SYS 2/2] arch-review: <id> ===

=== [SW 1/2] swreq: <id> ===                     (only if layer ran)
=== [REVIEW SW 1/2] req-review: <id> ===
=== [SW 2/2] swarch: <id> ===
=== [REVIEW SW 2/2] arch-review: <id> ===

=== [COMPONENT 1/4] <req-key>: <id> ===          (only if layer ran)
=== [REVIEW COMPONENT 1/4] req-review: <id> ===
=== [COMPONENT 2/4] arch: <id> ===
=== [REVIEW COMPONENT 2/4] arch-review: <id> ===
=== [COMPONENT 3/4] tc: <id> ===
=== [REVIEW COMPONENT 3/4] vplan-review: <id> ===
=== [COMPONENT 4/4] fmea: <id> ===

=== [FLOW SUMMARY] ===
<summary JSON>
```

Each `[REVIEW …]` block is omitted only when its corresponding draft step was skipped or
failed.

**Flow summary shape:**

```json
{
  "feature_context_summary": "one sentence",
  "stages_run": ["safety_v", "sys", "sw", "component"],
  "stages_skipped": [],
  "skip_reasons": {
    "<stage>": "auto-detect: catalog does not declare <missing types>"
  },
  "artefacts": {
    "safety_v": {
      "hazard":       {"id": "hazard__...",       "overall": "pass|needs_work|fail"},
      "safety_goal":  {"id": "safety_goal__...",  "overall": "pass|needs_work|fail"},
      "fsr":          {"id": "fsr__...",          "overall": "pass|needs_work|fail"}
    },
    "sys": {
      "sysreq":   {"id": "sysreq__...",   "overall": "pass|needs_work|fail"},
      "sys-arch": {"id": "sys_arch__...", "overall": "pass|needs_work|fail"}
    },
    "sw": {
      "swreq":  {"id": "swreq__...",  "overall": "pass|needs_work|fail"},
      "swarch": {"id": "swarch__...", "overall": "pass|needs_work|fail"}
    },
    "component": {
      "req":  {"id": "<req-key>__...", "overall": "pass|needs_work|fail"},
      "arch": {"id": "arch__...",      "overall": "pass|needs_work|fail"},
      "tc":   {"id": "tc__...",        "overall": "pass|needs_work|fail"},
      "fmea": {"id": "fmea__...",      "rpn": 160}
    }
  },
  "stop_reason": null
}
```

When a layer is skipped, its key in `artefacts` is omitted and the layer name appears in
`stages_skipped` with the reason in `skip_reasons`. When the chain stops early (Guardrail
G3), `stop_reason` carries the diagnostic from the failing skill.

---

## Process

### Step 0: Validate inputs

Confirm `feature_context` and `parent_link` are provided. If either is missing, FAIL before
invoking any sub-skill:

```
FAIL: pharaoh-flow requires feature_context and parent_link.
Provide both before invoking the orchestrator.
```

If the caller supplied `stages`, validate every entry against the allowed set
(`safety_v`, `sys`, `sw`, `component`). Unknown values FAIL.

---

### Step 1: Resolve which layers will run

Read `.pharaoh/project/artefact-catalog.yaml`. For each layer, mark it `present-in-catalog`
when **every** required type for that layer is declared:

| Layer | Required catalog keys |
|---|---|
| `safety_v` | `hazard`, `safety_goal`, `fsr` |
| `sys` | `sysreq`, `sys-arch` |
| `sw` | `swreq`, `swarch` |
| `component` | one of (`req`, `comp_req`, `gd_req`), plus `arch`, `tc`. (`fmea` is best-effort and may be absent — see Step 6 of the component layer.) |

Selection rules:

- **No `stages` argument (auto-detect)** — every layer where `present-in-catalog` is true
  runs; layers whose types are not declared are silently skipped, with `skip_reasons["<layer>"]
  = "auto-detect: catalog does not declare <missing types>"`.
- **Explicit `stages` argument** — only requested layers run; layers not requested record
  `skip_reasons["<layer>"] = "not requested by caller"`. For every requested layer that is
  NOT `present-in-catalog`, FAIL hard:

  ```
  FAIL: stages argument requested "<layer>" but artefact-catalog.yaml does not
  declare the required types: <missing types>.
  Either declare the types in the catalog (run pharaoh-tailor-fill), or remove
  "<layer>" from the stages argument.
  ```

If neither auto-detect nor an explicit `stages` argument selects any layer, FAIL:

```
FAIL: no layers selected. Catalog declares none of {safety_v, sys, sw, component}
artefact types and the caller did not pass a stages argument.
```

For the `component` layer, also resolve which requirement key to use (the first of
`req` / `comp_req` / `gd_req` declared in the catalog wins). Record the chosen key as
`<req-key>` and use it consistently throughout the layer.

---

### Step 2: Run the safety_v layer (if selected)

For each stage in order — `hazard`, `safety_goal`, `fsr` — invoke `pharaoh-req-draft` with
`target_level=<stage>`, then `pharaoh-req-review` on the drafted RST.

Inputs forwarded to `pharaoh-req-draft`:

| Stage | feature_context | parent_link |
|---|---|---|
| `hazard` | the user's `feature_context` | the user's `parent_link` |
| `safety_goal` | "Safety goal addressing hazard `<hazard-id>`: …" — derived from the user's `feature_context` and the hazard ID emitted in the prior step | the `hazard` ID |
| `fsr` | "Functional safety requirement deriving safety goal `<safety_goal-id>`: …" | the `safety_goal` ID |

Forward `safety_context` to every step. The drafter uses the catalog's `required_links`
(e.g. `derives_from`, `safety_goal_for`) to attach the correct link relation; the
orchestrator does not hardcode link names.

Capture the IDs emitted by the layer; the `fsr` ID becomes the parent for the SYS layer's
`sysreq` (if SYS runs). If the SYS layer is skipped, the `fsr` ID becomes the parent for the
SW layer's `swreq` (if SW runs). If SYS and SW are both skipped, the `fsr` ID becomes the
parent for the `component` layer's requirement.

Review-policy: a `pharaoh-req-review` returning `overall: needs_work` or `overall: fail` does
NOT stop the chain (Guardrail G4). A hard FAIL from `pharaoh-req-draft` does (Guardrail G3).

---

### Step 3: Run the sys layer (if selected)

Step 3a — `pharaoh-req-draft` with `target_level=sysreq`. Parent is whichever upstream ID
was last produced (the `fsr` ID when safety-V ran, otherwise the user's `parent_link`).

Step 3b — `pharaoh-req-review` on the `sysreq`.

Step 3c — `pharaoh-arch-draft` with `target_level=sys-arch`. Parent is the `sysreq` ID.

Step 3d — `pharaoh-arch-review` on the `sys-arch`.

Capture both IDs. The `sys-arch` ID is the upstream parent for the SW layer (if SW runs); when
SW is skipped, the `sys-arch` ID becomes the parent for the `component` layer's requirement.

---

### Step 4: Run the sw layer (if selected)

Step 4a — `pharaoh-req-draft` with `target_level=swreq`. Parent is whichever upstream ID was
last produced (`sys-arch` when SYS ran, `fsr` when safety-V ran without SYS, or the user's
`parent_link` otherwise).

Step 4b — `pharaoh-req-review` on the `swreq`.

Step 4c — `pharaoh-arch-draft` with `target_level=swarch`. Parent is the `swreq` ID.

Step 4d — `pharaoh-arch-review` on the `swarch`.

Capture both IDs. The `swarch` ID is the upstream parent for the `component` layer's
requirement (if the `component` layer runs).

---

### Step 5: Run the component layer (if selected)

This is the classical chain preserved from the prior behaviour, with an explicit review pass
after every drafted artefact (req, arch, tc) and an FMEA at the end.

Step 5a — `pharaoh-req-draft` with `target_level=<req-key>` (the key resolved in Step 1).
Parent is the closest upstream ID — `swarch` when SW ran, else `sys-arch` when SYS ran, else
`fsr` when safety_V ran, else the user's `parent_link`.

Step 5b — `pharaoh-req-review` on the requirement.

Step 5c — `pharaoh-arch-draft` with `target_level=arch` and the requirement's ID as parent.

Step 5d — `pharaoh-arch-review` on the architecture element.

Step 5e — `pharaoh-vplan-draft` with `target_level=tc` and the requirement's ID as parent.

Step 5f — `pharaoh-vplan-review` on the test case.

Step 5g — `pharaoh-fmea` with `parent_id=<requirement-id>` and the user's `safety_context`.

For Steps 5e (vplan-draft) and 5g (fmea), a hard FAIL emits a `=== [WARNING …] ===` block but
does NOT stop the chain — the artefact is recorded as `null` in the summary. Steps 5a and
5c (the load-bearing draft steps) DO stop the chain on hard FAIL, per Guardrail G3.

---

### Step 6: Emit all outputs and the flow summary

Emit each artefact and review block in the order shown in the Outputs section. Emit the
flow summary last. List every layer that ran in `stages_run` and every layer that was
skipped in `stages_skipped`, with the reason recorded under `skip_reasons`.

---

## Guardrails

**G1 — Missing required inputs**

`feature_context` or `parent_link` absent → FAIL before any sub-skill runs (Step 0).

**G2 — Explicit stages argument referencing un-declared types**

When the caller passes `stages` and a requested layer's types are not declared in
`artefact-catalog.yaml`, FAIL hard with the missing types listed (Step 1). Auto-detect
silently skips a missing layer; an explicit request never falls back silently.

**G3 — Hard failure in a load-bearing draft step**

Within each layer, the draft skills are load-bearing. A hard FAIL from any
`pharaoh-req-draft` or `pharaoh-arch-draft` invocation stops the chain at that point and
records `stop_reason` with the failing skill name and its diagnostic. The vplan and fmea
steps in the `component` layer are best-effort (warnings but not chain stops).

**G4 — Review findings don't block the chain**

A review returning `overall: needs_work` or `overall: fail` is informational. The chain
continues. Action items are preserved in the review block for the user to address. The
orchestrator never auto-regenerates; that requires `pharaoh-req-regenerate`.

**G5 — Tailoring unavailable**

If `.pharaoh/project/` tailoring files are missing, the sub-skills will fail. Fail fast
with:

```
FAIL: pharaoh-flow cannot run without tailoring files at .pharaoh/project/.
Run pharaoh-tailor-detect → pharaoh-tailor-fill first.
```

**G6 — Catalog declares safety-V partial set**

A project that declares only some of `hazard`, `safety_goal`, `fsr` is mis-tailored. In
auto-detect mode the safety_v layer skips with reason
`auto-detect: catalog declares only <subset>; safety_v layer requires the full set`.
In explicit-stages mode this is a hard FAIL via Guardrail G2.

---

## Advisory chain

This skill has `chains_to: []` — it is a terminal orchestrator. After the flow summary,
advise only when reviews returned action items:

```
Review action items in the [REVIEW …] blocks above.
Use `pharaoh-req-regenerate` or `pharaoh-arch-draft` (with corrections) to address them.
```

---

## Worked example — safety-V on a project that declares the full V

**User input:**

> feature_context: "Unintended ABS pump activation while the brake pedal is released can
> destabilise the vehicle on slippery surfaces. The brake controller must prevent activation
> outside the slip-detection window."
> parent_link: `wf__brake_system_design`
> safety_context: ASIL B
> stages: (omitted — auto-detect)

The project's `artefact-catalog.yaml` declares `hazard`, `safety_goal`, `fsr`, `sysreq`,
`sys-arch`, `swreq`, `swarch`, `comp_req`, `arch`, `tc`. All four layers will run.

**Layer 1 — safety_v:**

- `pharaoh-req-draft` (target_level=hazard) emits `hazard__unintended_abs_pump_activation`,
  parent `wf__brake_system_design`, body describes the hazardous event.
- `pharaoh-req-draft` (target_level=safety_goal) emits
  `safety_goal__no_unintended_abs_activation` linked via `:derives_from:` to the hazard.
- `pharaoh-req-draft` (target_level=fsr) emits `fsr__abs_activation_window_check` linked via
  `:safety_goal_for:` to the safety goal.
- Each is reviewed by `pharaoh-req-review`; all three pass.

**Layer 2 — sys:**

- `sysreq__abs_activation_window_check` derives from `fsr__abs_activation_window_check`.
- `sys_arch__brake_controller_supervision` satisfies the sysreq.
- Both reviewed.

**Layer 3 — sw:**

- `swreq__pedal_state_gate` derives from `sys_arch__brake_controller_supervision`.
- `swarch__abs_supervision_module` satisfies the swreq.
- Both reviewed.

**Layer 4 — component:**

- `comp_req__abs_pump_activation` (the `<req-key>` resolved to `comp_req`) derives from
  `swarch__abs_supervision_module`.
- `arch__abs_pump_driver` satisfies the comp_req.
- `tc__abs_pump_activation_001` verifies the comp_req.
- `fmea__abs_pump_activation__no_activation` derived from the comp_req; RPN = 160.

**Flow summary (condensed):**

```
=== [FLOW SUMMARY] ===
{
  "feature_context_summary": "Prevent unintended ABS pump activation outside slip window (ASIL B)",
  "stages_run": ["safety_v", "sys", "sw", "component"],
  "stages_skipped": [],
  "skip_reasons": {},
  "artefacts": {
    "safety_v": {
      "hazard":      {"id": "hazard__unintended_abs_pump_activation",  "overall": "pass"},
      "safety_goal": {"id": "safety_goal__no_unintended_abs_activation","overall": "pass"},
      "fsr":         {"id": "fsr__abs_activation_window_check",        "overall": "pass"}
    },
    "sys": {
      "sysreq":   {"id": "sysreq__abs_activation_window_check",     "overall": "pass"},
      "sys-arch": {"id": "sys_arch__brake_controller_supervision",  "overall": "pass"}
    },
    "sw": {
      "swreq":  {"id": "swreq__pedal_state_gate",         "overall": "pass"},
      "swarch": {"id": "swarch__abs_supervision_module",  "overall": "pass"}
    },
    "component": {
      "req":  {"id": "comp_req__abs_pump_activation",            "overall": "pass"},
      "arch": {"id": "arch__abs_pump_driver",                    "overall": "pass"},
      "tc":   {"id": "tc__abs_pump_activation_001",              "overall": "pass"},
      "fmea": {"id": "fmea__abs_pump_activation__no_activation", "rpn": 160}
    }
  },
  "stop_reason": null
}
```

---

## Worked example — classical V on a project without safety-V or SYS/SWE split

**User input:**

> feature_context: "The brake controller shall engage the ABS pump when wheel slip exceeds a
> calibrated threshold. Target level: component."
> parent_link: `wf__brake_system_design`
> safety_context: ASIL B
> stages: (omitted — auto-detect)

The project's catalog declares only `gd_req`, `arch`, `tc`. Auto-detect skips `safety_v`,
`sys`, and `sw`; only the `component` layer runs.

**Layer 4 — component (only):**

- `gd_req__abs_pump_activation` parent `wf__brake_system_design`.
- `arch__brake_controller_abs_module` satisfies the requirement.
- `tc__abs_pump_activation_001` verifies the requirement.
- `fmea__abs_pump_activation__no_activation` derived from the requirement; RPN = 160.

**Flow summary:**

```
=== [FLOW SUMMARY] ===
{
  "feature_context_summary": "Brake controller engages ABS pump on wheel-slip threshold exceedance (ASIL B)",
  "stages_run": ["component"],
  "stages_skipped": ["safety_v", "sys", "sw"],
  "skip_reasons": {
    "safety_v": "auto-detect: catalog does not declare hazard, safety_goal, fsr",
    "sys":      "auto-detect: catalog does not declare sysreq, sys-arch",
    "sw":       "auto-detect: catalog does not declare swreq, swarch"
  },
  "artefacts": {
    "component": {
      "req":  {"id": "gd_req__abs_pump_activation",              "overall": "pass"},
      "arch": {"id": "arch__brake_controller_abs_module",        "overall": "pass"},
      "tc":   {"id": "tc__abs_pump_activation_001",              "overall": "pass"},
      "fmea": {"id": "fmea__abs_pump_activation__no_activation", "rpn": 160}
    }
  },
  "stop_reason": null
}
```

This is the prior behaviour of the skill, preserved exactly.

---

## Worked example — bootstrapping safety V in isolation

**User input:**

> feature_context: "Loss of brake pedal feedback while ABS is intervening can lead to a delayed
> driver response and longer stopping distances."
> parent_link: `wf__hara`
> safety_context: ASIL C
> stages: ["safety_v"]

Even though the project's catalog also declares `sys`, `sw`, and `component` types, the
caller restricts the run to the safety V — typical when bootstrapping HARA outputs before the
lower V is mature enough to chain.

Only Layer 1 runs: hazard → safety_goal → fsr, each reviewed. The `[FLOW SUMMARY]`
records `stages_run: ["safety_v"]`, `stages_skipped: ["sys", "sw", "component"]`, and a
`skip_reasons` map indicating each was skipped because the caller did not request it.

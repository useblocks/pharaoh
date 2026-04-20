# Strictness and Workflow Enforcement Instructions

These instructions tell you how to handle workflow gates and session state.
Follow these steps when a skill needs to check prerequisites or record progress.

---

## 0. Who performs these checks

Session-state gating (`.pharaoh/session.json` reads and writes, enforcing-mode blocking,
advisory-mode tips) is an **orchestrator concern**, not an atomic-primitive concern.

**Atomic skills** (single-artefact primitives: `pharaoh:req-draft`,
`pharaoh:arch-draft`, `pharaoh:vplan-draft`, `pharaoh:fmea`, `pharaoh:req-review`,
`pharaoh:arch-review`, `pharaoh:vplan-review`, etc.) execute their defined operation
exactly once and emit their defined output. They do **not** read `pharaoh.toml`, do **not**
consult `.pharaoh/session.json`, and do **not** block on gate conditions. This keeps them
indivisible (atomicity criterion a) and composable into arbitrary flows.

**Orchestrator / composite skills** (`pharaoh:flow`, `pharaoh:audit-fanout`,
`pharaoh:reqs-from-module`, `pharaoh:plan`, `pharaoh:change`, `pharaoh:release`, and the
legacy top-level skills `pharaoh:decide`, `pharaoh:spec`, `pharaoh:mece`, `pharaoh:trace`,
`pharaoh:setup`) are responsible for:

1. Reading `pharaoh.toml` and determining the strictness level (Section 1).
2. Reading `.pharaoh/session.json` to check whether gate prerequisites are met
   (Sections 3 and 4).
3. Blocking in enforcing mode when a gate fails, or emitting a tip in advisory mode
   (Sections 2 and 3).
4. Dispatching the relevant atomic primitives when gates pass.
5. Writing back to `.pharaoh/session.json` on successful completion (Section 4d).

The rest of this document describes *what* the checks are. *Where* they run: in
orchestrators. Atomic primitives ignore these rules.

---

## 1. Read Strictness Configuration

### Step 1a: Find pharaoh.toml

Look for `pharaoh.toml` in the workspace root (the same directory as `ubproject.toml` or `conf.py`).

- If `pharaoh.toml` exists, read the `[pharaoh]` section.
- If `pharaoh.toml` does not exist, use advisory mode for all settings. Skip to Section 2.

### Step 1b: Parse strictness level

Read the `strictness` key from `[pharaoh]`:

```toml
[pharaoh]
strictness = "advisory"   # or "enforcing"
```

- `"advisory"` (default): Skills suggest the recommended workflow but never block the user.
- `"enforcing"`: Skills check prerequisites and block if they are not met.

If the `strictness` key is missing or has any value other than `"enforcing"`, treat it as `"advisory"`.

### Step 1c: Parse workflow gates

Read `[pharaoh.workflow]` for gate configuration:

```toml
[pharaoh.workflow]
require_change_analysis = true    # any authoring skill requires pharaoh:change
require_verification = true       # pharaoh:release requires any review skill
require_mece_on_release = false   # pharaoh:release requires pharaoh:mece
```

These gates only have effect when `strictness = "enforcing"`. In advisory mode, they are used only for tip messages.

Default values if keys are missing:
- `require_change_analysis = true`
- `require_verification = true`
- `require_mece_on_release = false`

### Step 1d: Parse traceability requirements

Read `[pharaoh.traceability]` for required link chains:

```toml
[pharaoh.traceability]
required_links = [
    "req -> spec",
    "spec -> impl",
    "impl -> test",
]
```

Each entry defines that every need of the source type should have at least one outgoing link to a need of the target type. These are used by pharaoh:mece for gap analysis and by any review skill for completeness checks.

If `required_links` is missing or empty, no traceability chains are enforced.

---

## 2. Advisory Mode Behavior

When `strictness = "advisory"` (or when `pharaoh.toml` is absent):

### Rules

- Never block the user from proceeding with any skill.
- Never refuse to execute a skill because a prerequisite was not met.
- Always complete the requested task.

### Tips

When a recommended prerequisite was not completed, present a brief tip after the skill's output. Format tips as:

```
Tip: Consider running pharaoh:change first to understand the impact before authoring new needs.
```

Specific tips by skill:

| Current skill | Missing prerequisite | Tip message |
|---|---|---|
| any authoring skill | No change analysis done | `Tip: Consider running pharaoh:change first to understand the impact of this modification.` |
| `pharaoh:release` | No verification done | `Tip: Consider running any review skill (e.g. pharaoh:req-review) to validate before release.` |
| `pharaoh:release` | No MECE check done | `Tip: Consider running pharaoh:mece to check for gaps before release.` |

### When to show tips

Only show a tip if:
1. The workflow gate is configured (either in `pharaoh.toml` or by default).
2. The prerequisite skill has not been run in the current session (check session state if it exists).
3. The tip is relevant to what the user is doing.

Do not show tips repeatedly. If you already showed a tip and the user proceeded, do not show it again in the same session.

---

## 3. Enforcing Mode Behavior

When `strictness = "enforcing"`:

### Rules

- Check all relevant prerequisites before executing a skill.
- If a prerequisite is not met, block execution with a clear message.
- Do not partially execute the skill. Stop at the gate check.

### Gate checks

Before executing a skill, check the following gates:

**Any authoring skill** gate (e.g. pharaoh:req-draft, pharaoh:arch-draft, pharaoh:vplan-draft):
1. Read session state (see Section 4).
2. If `require_change_analysis = true`:
   - Check if `pharaoh:change` was run for the relevant needs.
   - The change analysis must be `acknowledged = true` in session state.
   - If not met, block with:
     ```
     Blocked: Change analysis required before authoring.
     Run pharaoh:change for the affected requirements first.
     ```

**pharaoh:release** gate:
1. Read session state.
2. If `require_verification = true`:
   - Check if any review skill (e.g. pharaoh:req-review) was run and passed.
   - The verification must show `verified = true` in session state.
   - If not met, block with:
     ```
     Blocked: Verification required before release.
     Run the appropriate review skill (e.g. pharaoh:req-review) to validate implementations first.
     ```
3. If `require_mece_on_release = true`:
   - Check if `pharaoh:mece` was run.
   - The MECE check must show `mece_checked = true` in session state.
   - If not met, block with:
     ```
     Blocked: MECE analysis required before release.
     Run pharaoh:mece to check for gaps first.
     ```

### Default gate summary

| Skill | Requires | Condition |
|---|---|---|
| any authoring skill | `pharaoh:change` acknowledged | `require_change_analysis = true` |
| `pharaoh:release` | any review skill passed | `require_verification = true` |
| `pharaoh:release` | `pharaoh:mece` checked | `require_mece_on_release = true` |

### Skills with no gates

The following skills have no prerequisites and execute freely in any mode:
- `pharaoh:setup`
- `pharaoh:change`
- `pharaoh:trace`
- `pharaoh:mece`
- `pharaoh:plan`
- All **review / audit skills** (they inspect existing artefacts and do not modify them):
  `pharaoh:req-review`, `pharaoh:arch-review`, `pharaoh:vplan-review`,
  `pharaoh:review-completeness`, `pharaoh:coverage-gap`,
  `pharaoh:standard-conformance`, `pharaoh:lifecycle-check`,
  `pharaoh:process-audit`, `pharaoh:tailor-review`
- All **read-only memory / context skills**: `pharaoh:context-gather`
- All **tailoring authoring skills** (they author `.pharaoh/project/` metadata, not
  sphinx-needs artefacts, and therefore are not subject to the authoring gate):
  `pharaoh:tailor-detect`, `pharaoh:tailor-fill`

---

## 4. Session State Management

Session state tracks workflow progress across skill invocations within a working session.

### Step 4a: State file location

The state file is `.pharaoh/session.json` in the workspace root.

- If the `.pharaoh/` directory does not exist, create it.
- If `session.json` does not exist, treat all states as empty (no prerequisites met).

### Step 4b: State file structure

```json
{
  "version": 1,
  "created": "2026-02-11T17:30:00Z",
  "updated": "2026-02-11T18:00:00Z",
  "changes": {
    "REQ_001": {
      "change_analysis": "2026-02-11T17:30:00Z",
      "acknowledged": true,
      "authored": false,
      "verified": false
    },
    "REQ_002": {
      "change_analysis": "2026-02-11T17:45:00Z",
      "acknowledged": true,
      "authored": true,
      "verified": false
    }
  },
  "global": {
    "mece_checked": false,
    "mece_timestamp": null,
    "last_release": null
  }
}
```

**Fields:**

- `version`: Schema version. Always `1` for now.
- `created`: ISO 8601 timestamp when the session was started.
- `updated`: ISO 8601 timestamp of the last update.
- `changes`: Dictionary keyed by need ID. Each entry tracks per-need workflow progress:
  - `change_analysis`: Timestamp of when pharaoh:change was run for this need. `null` if not run.
  - `acknowledged`: Boolean. True if the user acknowledged the change analysis results.
  - `authored`: Boolean. True if any authoring skill was used to modify this need.
  - `verified`: Boolean. True if any review skill passed for this need.
- `global`: Global workflow state not tied to a specific need:
  - `mece_checked`: Boolean. True if pharaoh:mece was run.
  - `mece_timestamp`: Timestamp of last MECE check. `null` if not run.
  - `last_release`: Timestamp of last pharaoh:release run. `null` if never run.

### Step 4c: Reading session state

When checking prerequisites:

1. Read `.pharaoh/session.json`.
2. If the file does not exist or is empty, treat all values as their zero state (`false`, `null`).
3. If the file contains malformed JSON, warn the user and treat as empty.
4. Check the relevant fields for the gate being evaluated.

For per-need gates (e.g., any authoring skill checking change analysis):
- Look up each affected need ID in the `changes` dictionary.
- If the need ID is not present, the prerequisite was not met.
- If the need ID is present, check the relevant boolean field.

For global gates (e.g., pharaoh:release checking MECE):
- Check the `global` section.

### Step 4d: Writing session state

After a skill completes successfully, update the session state:

1. Read the current `.pharaoh/session.json` (or start with an empty structure).
2. Update the relevant fields:

| After skill | Fields to update |
|---|---|
| `pharaoh:change` | Set `changes.<need_id>.change_analysis` to current timestamp. Set `acknowledged` to `true` if the user acknowledged the results. |
| any authoring skill | Set `changes.<need_id>.authored` to `true`. |
| any review skill | Set `changes.<need_id>.verified` to `true` for each verified need. |
| `pharaoh:mece` | Set `global.mece_checked` to `true`. Set `global.mece_timestamp` to current timestamp. |
| `pharaoh:release` | Set `global.last_release` to current timestamp. |

3. Set `updated` to the current ISO 8601 timestamp.
4. Write the updated JSON back to `.pharaoh/session.json`.

### Step 4e: Session lifecycle

- Session state is **ephemeral**. The `.pharaoh/` directory is gitignored.
- Do not assume session state persists across different terminal sessions or IDE restarts.
- If the user explicitly asks to reset workflow state, delete `.pharaoh/session.json`.
- Do not create `.pharaoh/session.json` at project setup time. Only create it when the first skill writes state.

---

## 5. Combining Advisory and Enforcing Across Skills

Use this decision flow at the start of any gated skill:

```
1. Read pharaoh.toml -> determine strictness level
2. If strictness = "advisory":
   a. Execute the skill fully
   b. After completion, check if a recommended prerequisite was skipped
   c. If skipped, show a single tip line
   d. Done
3. If strictness = "enforcing":
   a. Identify which gates apply to this skill
   b. Read .pharaoh/session.json
   c. For each gate, check if the prerequisite is met
   d. If any gate fails:
      - Print the "Blocked: ..." message
      - List specifically which prerequisites are missing
      - Name the skill command the user should run
      - Stop. Do not execute the skill.
   e. If all gates pass:
      - Execute the skill fully
      - Update session state on completion
      - Done
```

---

## 6. Edge Cases

### No pharaoh.toml and no session state

Everything runs in advisory mode. No tips are shown (there is nothing to suggest since defaults are permissive without explicit configuration).

### pharaoh.toml exists but strictness is not set

Default to `"advisory"`. Show tips based on workflow gate defaults.

### Session state references needs that no longer exist

Ignore stale entries. Do not error on need IDs that are not in the current needs index. They may have been deleted or renamed.

### User asks to bypass enforcing mode

If the user explicitly says to skip a gate check (e.g., "proceed anyway" or "skip the check"), respect the request. Log a warning:

```
Warning: Skipping change analysis gate at user request. Workflow compliance is not guaranteed.
```

Then execute the skill normally. Do not update session state to indicate the prerequisite was met.

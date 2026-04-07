---
name: pharaoh-decide
description: "Use when recording a design decision as a traceable sphinx-needs object with alternatives, rationale, and links to affected requirements"
---

# pharaoh-decide

Record design decisions as traceable sphinx-needs `decision` directives. Each decision captures the chosen option, rejected alternatives, rationale, and explicit links to the requirements or specifications it affects. This skill ensures every decision has proper `decided_by`, `alternatives`, and `rationale` fields, and delegates RST generation to `pharaoh:author` to avoid duplicating directive-writing logic.

---

## When to Use

- When a design choice has been made and must be recorded for traceability.
- When comparing alternatives for a requirement or specification and committing to one.
- When `pharaoh:spec` identifies a gap and calls this skill programmatically to record the resolution.
- When superseding an earlier decision with a new one.

## Prerequisites

- The workspace must contain at least one sphinx-needs project with a `decision` type configured.
- No workflow gates. This skill runs freely in both advisory and enforcing modes.

---

## Process

Execute the following steps in order.

---

### Step 1: Get Project Data

Follow the full detection and data access algorithm defined in `skills/shared/data-access.md`.

1. Detect project structure (project roots, source directories, configuration).
2. Read project configuration (need types, link types, ID settings).
3. Build the needs index using the best available data tier (ubc CLI, ubCode MCP, or raw file parsing).
4. Read `pharaoh.toml` for strictness level and workflow settings.

Present the detection summary before proceeding:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier used>
Needs found: <count>
Strictness: <advisory|enforcing>
```

#### Verify `decision` type exists

After reading the project configuration, confirm that a type with directive name `decision` is present in the types list.

If `decision` is not configured, show the user the exact TOML to add:

```toml
[[needs.types]]
directive = "decision"
title = "Decision"
prefix = "DEC_"
color = "#E8D0A9"
style = "node"
```

Also verify that these extra options are configured:

```toml
[needs.fields.decided_by]
description = "Who made the decision"

[needs.fields.alternatives]
description = "Rejected alternatives, semicolon-separated"

[needs.fields.rationale]
description = "Why this option was chosen"
```

And verify the `decides` link type exists:

```toml
[needs.extra_links.decides]
incoming = "is decided by"
outgoing = "decides for"
```

Ask the user to confirm before proceeding if any of these are missing.

---

### Step 2: Gather Decision Context

Determine what to record. The following pieces of information are required:

- **Title**: What is being decided (e.g., "Use CAN bus for brake pedal sensor").
- **Affected needs**: Need IDs for the `:decides:` link (e.g., `REQ_001, SPEC_001`).
- **decided_by**: Who made this decision. Default to `claude` when the AI is generating the decision autonomously. Ask the user otherwise.
- **alternatives**: Rejected alternatives, semicolon-separated (e.g., `SPI at 1MHz; Direct analog input`).
- **rationale**: Why this option was chosen over the alternatives.
- **status**: One of `proposed`, `accepted`, `superseded`, `rejected`.

#### When called standalone

Prompt the user for each missing piece. Do not proceed until all five fields (title, affected needs, decided_by, alternatives, rationale) are populated. If the user omits any field, ask for it explicitly.

#### When called by `pharaoh:spec`

Accept all context programmatically. Do not prompt. All required fields must be provided by the calling skill.

#### Status defaults

- **Standalone invocation**: Default status to `proposed`.
- **Called by `pharaoh:spec`**: Default status to `accepted`.

The user may override the default in either case.

---

### Step 3: Generate ID

Reuse `pharaoh:author` ID generation logic (Step 3 of pharaoh-author).

1. Check `pharaoh.toml` for `[pharaoh.id_scheme]`. If a pattern exists, apply it with `{TYPE}` resolving to `DEC`.
2. If no id_scheme is configured, infer the pattern from existing `decision` needs in the index. Look for `DEC_*` IDs and determine the numbering scheme.
3. If no existing decisions exist, use the prefix from the type configuration (e.g., `DEC_`) and start at `001`, padded to match `id_length`.
4. Validate uniqueness against the full needs index. If the generated ID already exists, increment until a unique ID is found.

---

### Step 4: Write the Need

Delegate to `pharaoh:author` with all fields populated. Provide the following directive structure to author:

```rst
.. decision:: <title>
   :id: <generated_id>
   :status: <proposed|accepted>
   :decides: <need_id1>, <need_id2>
   :decided_by: <name or claude>
   :alternatives: <alt1>; <alt2>
   :rationale: <why this option>

   <expanded description>
```

The expanded description should summarize the decision in one to three sentences, covering what was chosen and why the alternatives were rejected.

#### Superseding an existing decision

When a new decision replaces an old one:

1. Set the old decision's status to `superseded` using `pharaoh:author` modification logic.
2. On the new decision, add `:links: <old_dec_id>` to establish the supersession chain.
3. The new decision's description should reference the old decision ID and explain why it is being replaced.

---

### Step 5: File Placement

Place the decision in `decisions.rst` in the same directory as the affected requirements.

1. Identify the directory of the first need listed in `:decides:`. Use the needs index to find its file path.
2. Check if `decisions.rst` exists in that directory. If it does, append the new decision after the last existing `decision` directive in the file.
3. If `decisions.rst` does not exist, create it with a proper RST title:

```rst
Decisions
=========

.. decision:: <title>
   :id: <id>
   ...
```

4. If no `:decides:` links are specified (rare case), fall back to `pharaoh:author` file placement logic (Step 6 of pharaoh-author).

Delegate the actual file writing to `pharaoh:author`.

---

### Step 6: Update Session State

After successfully writing the decision:

1. Read `.pharaoh/session.json` (or initialize if it does not exist).
2. Create the `.pharaoh/` directory if it does not exist.
3. For the decision need ID, set `changes.<dec_id>.authored = true`:

```json
{
  "<dec_id>": {
    "change_analysis": null,
    "acknowledged": false,
    "authored": true,
    "verified": false
  }
}
```

4. Set `updated` to the current ISO 8601 timestamp.
5. Write the updated JSON back to `.pharaoh/session.json`.

---

### Step 7: Follow-up

#### Standalone invocation

After writing the decision, suggest the next step:

```
Next step: Run pharaoh:verify to validate the decision against its linked requirements.
```

#### Called by `pharaoh:spec`

Return the decision ID silently. Do not print follow-up suggestions. The calling skill manages the workflow.

---

## Strictness Behavior

Follow the instructions in `skills/shared/strictness.md`.

### Advisory mode

Execute freely. No gates. Decisions have no prerequisites and do not gate other skills. Do not show tips -- decisions can be recorded at any time without prior analysis.

### Enforcing mode

Execute freely. No gates. Decisions can be recorded at any time regardless of strictness level. This skill is gate-free in both modes.

Strictness has no effect on decision recording. Both modes follow the same process.

---

## Key Constraints

1. **All three fields are mandatory.** Always populate `decided_by`, `alternatives`, and `rationale`. If the user omits any of them, ask explicitly. Do not write a decision with missing fields.
2. **Default `decided_by` to `claude`** when the AI is making the decision autonomously (e.g., during `pharaoh:spec` execution).
3. **Default `status` to `proposed`** when standalone, `accepted` when called by `pharaoh:spec`.
4. **Superseding requires two writes.** When replacing an old decision, update the old decision's status to `superseded` AND add `:links:` on the new decision referencing the old one.
5. **Reuse `pharaoh:author` for RST writing.** Do not duplicate directive generation, file placement, or ID generation logic. Delegate to author for all file operations.
6. **Validate `:decides:` targets exist.** Every need ID in the `:decides:` field must exist in the needs index. If a target does not exist, warn the user and ask whether to proceed.
7. **Semicolons for alternatives.** Separate rejected alternatives with semicolons, not commas. Commas are reserved for need ID lists.

---

## Examples

### Example 1: Standalone decision recording

**User request**: "Record a decision that we chose PostgreSQL over MongoDB for the data store"

**Step 1** -- Data access detects:

```
Project: Backend Service (ubproject.toml)
Types: req, spec, impl, test, decision
Links: links, implements, tests, decides
Data source: Tier 3 (raw file parsing)
Needs found: 12
Strictness: advisory
```

**Step 2** -- Gather context. The user provided the title and one alternative. Prompt for missing fields:

```
Recording decision: "Use PostgreSQL for the data store"

Which requirements or specs does this decision affect?
> REQ_003, SPEC_005

Who is making this decision?
> engineering-lead

Any other rejected alternatives besides MongoDB?
> Redis as primary store

Why was PostgreSQL chosen over the alternatives?
> PostgreSQL provides ACID transactions and mature JSON support,
  which MongoDB and Redis cannot guarantee for our consistency requirements.
```

**Step 3** -- Generate ID. Existing decisions: DEC_001, DEC_002. Next ID: `DEC_003`.

**Step 4** -- Delegate to `pharaoh:author`. Directive written:

```rst
.. decision:: Use PostgreSQL for the data store
   :id: DEC_003
   :status: proposed
   :decides: REQ_003, SPEC_005
   :decided_by: engineering-lead
   :alternatives: MongoDB; Redis as primary store
   :rationale: PostgreSQL provides ACID transactions and mature JSON support required for data consistency

   Selected PostgreSQL over MongoDB and Redis. MongoDB lacks full ACID transaction
   support across collections. Redis does not provide durable storage guarantees
   suitable for a primary data store. PostgreSQL meets the consistency requirements
   defined in REQ_003.
```

**Step 5** -- Written to `docs/decisions.rst` (same directory as REQ_003).

**Step 6** -- Session state updated: `DEC_003.authored = true`.

**Step 7** -- Follow-up:

```
Next step: Run pharaoh:verify to validate the decision against its linked requirements.
```

---

### Example 2: Decision during spec generation (programmatic call)

`pharaoh:spec` identifies that no specification covers the communication protocol for subsystem X. It calls `pharaoh:decide` with all context provided:

- **Title**: "Use CAN bus for brake pedal sensor communication"
- **decides**: `REQ_001, SPEC_001`
- **decided_by**: `claude`
- **alternatives**: `SPI at 1MHz; Direct analog input`
- **rationale**: "CAN bus provides noise immunity required for safety-critical braking"
- **status**: `accepted`

`pharaoh:decide` executes without prompting:

1. Verifies `decision` type exists in configuration.
2. Generates ID: `DEC_004`.
3. Delegates to `pharaoh:author`:

```rst
.. decision:: Use CAN bus for brake pedal sensor communication
   :id: DEC_004
   :status: accepted
   :decides: REQ_001, SPEC_001
   :decided_by: claude
   :alternatives: SPI at 1MHz; Direct analog input
   :rationale: CAN bus provides noise immunity required for safety-critical braking

   Selected CAN bus over SPI and direct analog based on EMC requirements.
   SPI at 1MHz lacks sufficient noise immunity for the safety-critical braking
   subsystem. Direct analog input introduces unacceptable signal degradation
   over the required cable lengths.
```

4. Updates session state: `DEC_004.authored = true`.
5. Returns `DEC_004` to `pharaoh:spec`. No follow-up message printed.

---
name: pharaoh-verify
description: "Use when validating that implementations satisfy their linked requirements and specifications in a sphinx-needs project"
---

# pharaoh-verify

Verify that child needs actually satisfy their parent needs. This skill performs content-level verification -- reading the substance of each linked pair and assessing whether the child adequately addresses what the parent demands.

This is different from `pharaoh:mece`, which checks structural completeness (gaps, orphans, missing links). `pharaoh:verify` checks substance: does the spec truly satisfy the requirement? Does the test truly cover the implementation? In safety-critical domains (automotive, aerospace, medical devices), this kind of requirements satisfaction assessment must be demonstrated for compliance.

## When to Use

- Before a release, to confirm that all linked needs are substantively satisfied.
- After authoring new specifications, implementations, or test cases, to validate they address their parent requirements.
- During reviews of inherited or third-party requirements where traceability exists but satisfaction has not been assessed.
- When `pharaoh.toml` has `require_verification = true` and the project is in enforcing mode -- `pharaoh:release` will not proceed until verification passes.

## Prerequisites

- The workspace must contain at least one sphinx-needs project with needs that have links between them.
- `pharaoh:verify` has no workflow gates. It runs freely in both advisory and enforcing modes. No other Pharaoh skill is required before running this one.

---

## Process

Execute the following steps in order.

---

### Step 1: Get Project Data

Follow the full detection and data access algorithm defined in `skills/shared/data-access.md`.

1. Detect project structure (project roots, source directories, configuration).
2. Read project configuration (need types, link types, ID settings).
3. Build the needs index using the best available data tier (ubc CLI, ubCode MCP, or raw file parsing).
4. Build the link graph (bidirectional edges for all link types).
5. Read `pharaoh.toml` for strictness level, workflow gates, and traceability requirements.

Present the detection summary before proceeding:

```
Project: <project name>
Types: <comma-separated directive names>
Links: <comma-separated link option names>
Data source: <ubc CLI (version) | ubCode MCP | raw file parsing>
Needs found: <count>
Strictness: <advisory | enforcing>
```

If detection reveals issues (no project found, no needs, no links between needs), report clearly and ask the user for guidance.

---

### Step 2: Identify Verification Scope

Determine which parent-child pairs to verify. Ask the user or infer from context:

#### 2a. Full project verification

If the user asks to verify the entire project, or provides no specific scope:

- Collect every parent-child pair in the link graph.
- A pair consists of a parent need and a child need connected by any link type (`links`, `implements`, `verifies`, or any extra link).
- Report the total number of pairs before starting:

```
Full project verification scope:
  Total needs: <count>
  Linked pairs: <count>
  Link types involved: <comma-separated>

Proceed with verification? [yes/no]
```

For large projects (more than 50 pairs), suggest scoping to a subset first.

#### 2b. Specific need and its children

If the user specifies a need ID or a set of IDs:

- Find the specified need(s) in the index.
- Collect all direct children (needs that link TO the specified need as their parent, and needs that the specified need links TO as children).
- Walk the link direction based on the link type semantics:
  - For `links`: the need that has `:links: PARENT_ID` is the child.
  - For extra links like `implements`: the need with `:implements: PARENT_ID` is the child implementing the parent.
  - For extra links like `verifies` or `tests`: the need with `:verifies: PARENT_ID` is the child verifying the parent.
- Report the scope:

```
Verification scope for <NEED_ID>:
  Direct children: <count>
  Link types: <comma-separated>
  Pairs to verify: <count>
```

#### 2c. Recently authored needs

If the user asks to verify recent work, or if `.pharaoh/session.json` exists and contains needs with `authored = true` and `verified = false`:

- Read `.pharaoh/session.json`.
- Collect all need IDs where `authored = true` and `verified = false`.
- For each such need, find its parent(s) by following links in the reverse direction.
- Build the set of parent-child pairs that include at least one recently authored need.
- Report the scope:

```
Verification scope (recently authored needs):
  Authored needs pending verification: <count>
  Parent-child pairs to verify: <count>
```

If session state does not exist or has no unverified authored needs, fall back to asking the user for scope.

---

### Step 3: Pairwise Verification

For each parent-child pair in the verification scope, perform content-level assessment.

#### 3a. Read parent need content

Read the parent need's full content:
- Title (from the directive line)
- All options (status, tags, links, extra links)
- Full body text (the content block below the options)
- File path and line number (for reference in the report)

If using ubc CLI or ubCode MCP, the content is available in the needs index. If using raw file parsing, read the file at the recorded location and extract the full directive content including all indented body lines.

#### 3b. Read child need content

Read the child need's full content using the same approach as 3a.

#### 3c. Assess satisfaction

For each parent-child pair, evaluate the following criteria:

**Completeness** -- Does the child address ALL aspects of the parent?
- Identify the distinct requirements, constraints, or conditions stated in the parent.
- Check that each one is addressed (directly or by reasonable inference) in the child.
- If the parent states multiple conditions (e.g., "The system shall handle X and Y"), verify the child addresses both X and Y, not just one.

**Consistency** -- Are there contradictions between parent and child?
- Check for conflicting statements (e.g., parent says "at most 100ms", child says "within 200ms").
- Check for conflicting scope (e.g., parent covers all user roles, child only covers administrators).
- Check for conflicting priorities or severity levels.

**Specificity** -- Is the child specific enough to satisfy the parent?
- If the parent states a concrete requirement, the child should not be vaguer than the parent.
- If the parent says "100ms response time", the child should state a specific timing value, not just "fast response".
- Acceptable: child is MORE specific than parent (e.g., parent says "under 100ms", child says "under 50ms").

**Numeric consistency** -- Are quantitative values aligned?
- Compare all numeric values, thresholds, ranges, and units between parent and child.
- Flag any value in the child that exceeds, contradicts, or weakens a threshold in the parent.
- Examples of issues: parent says "99.9% uptime", child says "99% uptime"; parent says "maximum 10 retries", child says "unlimited retries".

#### 3d. Record pair result

After assessing each pair, record the result with the classification from Step 4.

---

### Step 4: Classify Results

Assign one of four classifications to each verified pair:

**PASS** -- The child adequately satisfies the parent.
- All aspects of the parent are addressed in the child.
- No contradictions exist.
- The child is at least as specific as the parent.
- Numeric values are consistent or stricter.

**PARTIAL** -- The child addresses some but not all aspects of the parent.
- At least one identifiable aspect of the parent is missing from the child.
- No direct contradictions exist (contradictions elevate to FAIL).
- The child is on the right track but incomplete.
- Include a note specifying which aspects are missing.

**FAIL** -- The child contradicts or does not meaningfully address the parent.
- The child contains a statement that directly conflicts with the parent.
- The child addresses a completely different concern than the parent.
- Numeric values in the child weaken or violate thresholds set by the parent.
- Include a note specifying the contradiction or gap.

**SKIP** -- Unable to assess the pair.
- The parent is too abstract to verify against (e.g., "The system shall be user-friendly").
- The child or parent has no meaningful body content (title only, empty body).
- The link type does not represent a satisfaction relationship (e.g., an informational cross-reference).
- Include a note explaining why the pair was skipped.

---

### Step 5: Schema Validation (if ubc is available)

If ubc CLI was detected as available in Step 1, run structural validation as a complement to the content-level verification.

#### 5a. Run ubc check

```
ubc check
```

Parse the output for errors and warnings. Record:
- Number of errors
- Number of warnings
- Specific issues (e.g., broken links, missing required fields, ID format violations)

#### 5b. Run ubc schema validate

```
ubc schema validate
```

Parse the output for ontology compliance issues. Record:
- Schema violations
- Type constraint violations
- Link constraint violations

#### 5c. Include in report

Add a "Schema Validation" section to the verification report with the results from 5a and 5b. Schema issues are separate from content-level verification but provide important structural context.

If ubc CLI is not available, skip this step entirely. Do not attempt to replicate ubc's validation logic manually. Note in the report:

```
Schema validation: skipped (ubc CLI not available)
```

---

### Step 6: Present Verification Report

Present the complete verification report to the user.

#### 6a. Results table

```
## Verification Report

### Results

| Parent | Child | Link Type | Result | Notes |
|--------|-------|-----------|--------|-------|
| REQ_001 | SPEC_001 | links | PASS | Spec addresses all timing and accuracy requirements |
| REQ_002 | SPEC_002 | links | PARTIAL | Missing wheel slip handling -- parent requires slip detection, child does not mention it |
| REQ_003 | SPEC_003 | implements | FAIL | Contradicts parent: parent requires 100ms response, child specifies 500ms |
| REQ_004 | SPEC_004 | links | SKIP | Parent is abstract ("system shall be reliable") -- no testable criteria |
```

Sort the table to show FAIL results first, then PARTIAL, then SKIP, then PASS. This puts actionable items at the top.

#### 6b. Summary counts

```
### Summary

- Verified: <total pairs> pairs
- PASS: <count>
- PARTIAL: <count>
- FAIL: <count>
- SKIP: <count>
```

#### 6c. Schema validation results (if available)

```
### Schema Validation (ubc)

- Errors: <count>
- Warnings: <count>
- Details:
  - <issue description 1>
  - <issue description 2>
```

Or if ubc was not available:

```
### Schema Validation

Skipped (ubc CLI not available). Install ubc for structural validation.
```

#### 6d. Recommendations

If any FAIL or PARTIAL results exist, provide specific recommendations:

```
### Recommendations

1. **SPEC_002** (PARTIAL): Add wheel slip detection logic to address REQ_002's
   slip handling requirement. The specification should describe the detection
   algorithm and thresholds.

2. **SPEC_003** (FAIL): The 500ms response time contradicts REQ_003's 100ms
   requirement. Either update the specification to meet the 100ms target or
   negotiate a change to REQ_003 with stakeholders.
```

Number the recommendations and reference the specific needs involved. Keep recommendations actionable -- state what needs to change in the child or what conversation needs to happen about the parent.

#### 6e. Overall verdict

At the end of the report, state the overall verification outcome:

- If all pairs are PASS or SKIP: `Verification PASSED. All assessed pairs satisfy their parent requirements.`
- If any pairs are PARTIAL but none are FAIL: `Verification PASSED WITH WARNINGS. <count> pair(s) have partial coverage. Review the PARTIAL results above.`
- If any pairs are FAIL: `Verification FAILED. <count> pair(s) have contradictions or critical gaps. These must be resolved before release.`

---

### Step 7: Update Session State

After presenting the report, update `.pharaoh/session.json` to record the verification results.

#### 7a. Read current session state

Read `.pharaoh/session.json` from the workspace root. If the file does not exist, initialize an empty structure:

```json
{
  "version": 1,
  "created": "<current ISO 8601 timestamp>",
  "updated": "<current ISO 8601 timestamp>",
  "changes": {},
  "global": {
    "mece_checked": false,
    "mece_timestamp": null,
    "last_release": null
  }
}
```

If the `.pharaoh/` directory does not exist, create it.

#### 7b. Update per-need verification status

For each need that was part of a verified pair (both parents and children):

- If the need ID already exists in `changes`, set `verified` to `true` only if ALL pairs involving that need received PASS.
- If any pair involving the need received PARTIAL or FAIL, set `verified` to `false`.
- SKIP results do not affect the `verified` flag (treat as if the pair was not assessed).
- If the need ID does not exist in `changes`, create an entry:

```json
{
  "change_analysis": null,
  "acknowledged": false,
  "authored": false,
  "verified": <true or false based on results>
}
```

#### 7c. Set timestamp

Set `updated` to the current ISO 8601 timestamp.

#### 7d. Write session state

Write the updated JSON back to `.pharaoh/session.json`.

Report what was updated:

```
Session state updated:
  Needs marked verified: <count>
  Needs marked not verified (PARTIAL/FAIL): <count>
```

#### 7e. Gate status for pharaoh:release

If `pharaoh.toml` has `require_verification = true`:

- Check if ALL needs in the project now have `verified = true` in the session state.
- If yes: `pharaoh:release gate: READY (all needs verified)`
- If no: `pharaoh:release gate: NOT READY (<count> needs not yet verified)`

If `require_verification` is false or `pharaoh.toml` does not exist, do not report gate status.

---

## Strictness Behavior

Follow the decision flow defined in `skills/shared/strictness.md`.

### Advisory mode (default)

- `pharaoh:verify` always runs fully regardless of what other skills have or have not been run.
- After completing verification, if the user has not run `pharaoh:change` for needs that failed verification, show a tip:

```
Tip: Consider running pharaoh:change for the needs that failed verification to understand the full impact before making corrections.
```

- Never block the user from proceeding.

### Enforcing mode

- `pharaoh:verify` itself has no prerequisites and is never blocked. It appears in the "Skills with no gates" list in `skills/shared/strictness.md`.
- However, its results gate `pharaoh:release`. When `require_verification = true` in enforcing mode:
  - `pharaoh:release` will check `.pharaoh/session.json` for `verified = true` on all relevant needs.
  - If any need has `verified = false` or is missing from the session state, `pharaoh:release` will block with:

```
Blocked: Verification required before release.
Run pharaoh:verify to validate implementations first.
```

- The verification report's overall verdict (PASSED, PASSED WITH WARNINGS, FAILED) determines which needs get `verified = true` in the session state.
- Only PASS results set `verified = true`. PARTIAL and FAIL results set `verified = false`.
- SKIP results leave the `verified` field unchanged from its previous value.

---

## Key Constraints

1. **Verify content, not structure.** This skill reads the body text of needs and assesses semantic satisfaction. It does not re-implement structural checks that `pharaoh:mece` or `ubc check` already provide.
2. **Be explicit about uncertainty.** When a parent requirement is ambiguous or abstract, classify the pair as SKIP rather than guessing. State why the pair was skipped.
3. **Never fabricate requirement content.** Base all assessments on what is actually written in the need directives. Do not infer unstated requirements or assume intent beyond what the text says.
4. **Present FAIL and PARTIAL results first.** The report table must be sorted so actionable items appear at the top. Reviewers should not have to scroll past dozens of PASS results to find problems.
5. **Recommendations must be actionable.** Do not just say "fix the contradiction." State what specifically needs to change in which need, or what stakeholder conversation needs to happen.
6. **Always update session state.** Even if all pairs pass, write the verification results to `.pharaoh/session.json`. This is required for the `pharaoh:release` gate to work correctly in enforcing mode.
7. **Do not modify need source files.** This skill is read-only with respect to the documentation. It reads needs and reports findings. Actual corrections are made by the user or by `pharaoh:author`.

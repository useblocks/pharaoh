---
name: pharaoh-mece
description: "Use when checking for gaps, redundancies, and inconsistencies in sphinx-needs requirements, or validating traceability completeness"
---

# pharaoh:mece -- MECE Analysis

Analyze a sphinx-needs project for structural completeness and consistency.
MECE stands for Mutually Exclusive, Collectively Exhaustive. This skill finds
gaps in traceability coverage (not exhaustive), redundant or overlapping
requirements (not mutually exclusive), and status or ID inconsistencies across
the needs set.

## 1. Overview

### What this skill does

- **Gap analysis**: Finds needs that are missing required downstream coverage
  (e.g., a requirement with no linked specification).
- **Orphan detection**: Finds needs that are completely disconnected from the
  traceability graph, or that terminate unexpectedly.
- **Redundancy analysis**: Flags needs of the same type with very similar titles,
  content, or identical link structures that may be unintentional duplicates.
- **Status inconsistency checks**: Detects contradictions between a need's status
  and the statuses of its linked parents or children.
- **ID scheme validation**: Ensures all need IDs conform to the project's naming
  convention and that no duplicates exist.
- **Schema validation**: When ubc CLI is available, runs full ontology and lint
  checks.

### How it differs from review skills (e.g. pharaoh:req-review)

Review skills (e.g. `pharaoh:req-review`) check the **content** of individual needs -- whether the
requirement text is clear, whether test cases adequately cover what they claim,
whether implementations match their specifications.

`pharaoh:mece` checks the **structure** of the requirements set as a whole --
whether every need is connected to the traceability chain, whether the chain has
gaps, and whether the set is internally consistent.

Both skills are complementary. Running them together gives full coverage of
content quality and structural integrity.

### Why it matters

In safety-critical domains (ISO 26262, IEC 62304, DO-178C, A-SPICE), regulatory
audits require evidence of complete bidirectional traceability from top-level
requirements through specifications, implementations, and tests. A single orphan
requirement or broken link chain can result in audit findings. This skill
automates the structural checks that catch these problems before an auditor does.

---

## 2. Process

Follow these steps in order. Do not skip steps. If a step fails or produces no
data, note that in the final report and continue to the next step.

---

### Step 1: Get project data

Follow the instructions in `skills/shared/data-access.md` completely. At the
end of data access you must have:

1. **Project roots**: All identified project root paths.
2. **Source directories**: Documentation source path for each project.
3. **Need types**: List of valid directive types with their prefixes (e.g.,
   `req`, `spec`, `impl`, `test`).
4. **Link types**: Standard `links` plus all extra_link names (e.g.,
   `implements`, `tests`).
5. **Data access tier**: Which tier is active (ubc CLI / ubCode MCP / raw files).
6. **Needs index**: Complete index of all needs with IDs, types, titles,
   statuses, links, content, and source file locations.
7. **Link graph**: Bidirectional graph of need relationships.
8. **Codelinks status**: Whether sphinx-codelinks is configured.
9. **Pharaoh config**: Strictness level, workflow gates, traceability
   requirements.

Read `pharaoh.toml` and extract the `[pharaoh.traceability]` section. Record
the `required_links` array. These rules drive gap analysis in Step 2.

If `pharaoh.toml` does not exist or `required_links` is missing/empty, use the
following defaults based on the detected need types:

- If `req` and `spec` types exist: `"req -> spec"`
- If `spec` and `impl` types exist: `"spec -> impl"`
- If `impl` and `test` types exist: `"impl -> test"`

Only apply default rules for type pairs that actually exist in the project
configuration. Do not assume types that are not configured.

Present the data access summary before proceeding:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier and version>
Needs found: <count>
Strictness: <advisory or enforcing>
Required chains: <list of required_links rules>
```

---

### Step 2: Gap analysis (Collectively Exhaustive)

For each rule in the `required_links` list (or the defaults from Step 1):

1. Parse the rule. Each rule has the form `"<source_type> -> <target_type>"`
   (e.g., `"req -> spec"`).
2. Find all needs whose `type` matches `<source_type>`.
3. For each source need, check whether it has at least one outgoing link
   (through any link type: `links`, `implements`, `tests`, or any extra_link)
   to a need whose `type` matches `<target_type>`.
4. A source need that has **no** outgoing link to any need of the target type
   is a **gap**.

When checking links, resolve them transitively only one level deep. That is,
check direct links only. Do not follow chains (e.g., if `req -> spec -> impl`
are two separate rules, check each rule independently).

When checking link targets, match on the **type** of the target need, not on
the ID prefix. Look up each linked ID in the needs index and check its `type`
field.

Record each gap as:

- Source need ID
- Source need type
- Missing target type
- The rule that requires the link (e.g., `"req -> spec"`)

If ubc CLI is available, also run `ubc check` and incorporate any traceability
warnings it reports. Merge ubc results with the file-based analysis to avoid
duplicates.

---

### Step 3: Orphan detection

Scan the needs index and link graph to classify each need:

**Completely disconnected (orphans)**:
A need that has NO incoming links AND no outgoing links of any kind. It is
entirely isolated from the traceability graph.

**Dead ends**:
A need that has incoming links but no outgoing links. This is expected for
**leaf types** -- types that sit at the end of the traceability chain (typically
test cases, or top-level requirements that have no parent). It is unexpected for
**intermediate types** (e.g., a specification with no implementation link).

Determine leaf types from the `required_links` rules:
- A type that never appears as a `<source_type>` in any rule is a leaf type.
  Example: if the rules are `req -> spec`, `spec -> impl`, `impl -> test`,
  then `test` is a leaf type because it never appears on the left side.
- A type that never appears as a `<target_type>` in any rule is a root type.
  Example: `req` is a root type because it never appears on the right side.

Classification:

| Condition | Root type | Intermediate type | Leaf type |
|---|---|---|---|
| No incoming, no outgoing | Orphan (warning) | Orphan (error) | Orphan (error) |
| Has incoming, no outgoing | N/A (root has no incoming by definition) | Dead end (error) | Expected (ok) |
| No incoming, has outgoing | Expected (ok) | Missing parent (warning) | Unexpected parent (info) |
| Has incoming, has outgoing | Unexpected (info) | Expected (ok) | Unexpected (info) |

Record each finding with:
- Need ID
- Need type
- Title
- Issue description
- Severity (error, warning, info)

---

### Step 4: Redundancy analysis (Mutually Exclusive)

Check for potential duplicates within each need type. Compare needs of the
**same type** only -- needs of different types are expected to have related
content (e.g., a spec that mirrors a req is correct, not redundant).

**Title similarity**:
For each pair of needs of the same type, compare their titles. Flag pairs where:
- Titles are identical (after normalizing whitespace and case).
- Titles differ only by a trailing number or minor suffix (e.g.,
  "User login" vs "User login v2").

**Content similarity**:
For each pair of needs of the same type, compare their content bodies. Flag
pairs where:
- Content is identical or nearly identical (ignoring whitespace differences).
- One content body is a strict subset of the other.

**Structural similarity**:
For each pair of needs of the same type, compare their link sets. Flag pairs
where:
- Both needs link to the exact same set of parent needs AND the exact same set
  of child needs.

Do not attempt full semantic analysis. Use string-level comparison only. The
goal is to surface obvious duplicates that a human reviewer should evaluate.

For each potential redundancy, record:
- Need A ID
- Need B ID
- Similarity type (title, content, structural)
- Brief reason (e.g., "Identical titles", "Same link set")

Always flag redundancies as **informational**. Redundancy may be intentional.
Never suggest automatic resolution.

---

### Step 5: Status inconsistencies

Check for contradictions between the statuses of linked needs. These checks
apply regardless of the link type used.

**Parent closed, child open**:
If a parent need has status matching any of `closed`, `done`, `verified`,
`approved` (case-insensitive), but a child need linked from it has status
matching any of `open`, `draft`, `in_progress`, `todo` (case-insensitive),
flag the inconsistency. The parent appears complete, but work remains on its
child.

**Child closed, parent open**:
If all children of a need have a closed-family status, but the parent itself
has an open-family status, flag it. The parent may be ready to close.

**Status vs. link existence**:
- A need with status `implemented` (or similar) that has no outgoing link to
  any `impl`-type need is suspicious.
- A need with status `verified` or `tested` that has no outgoing link to any
  `test`-type need is suspicious.
- Only flag these if the relevant need types exist in the project configuration.

For each inconsistency, record:
- Need ID
- Current status
- Issue description
- Severity (warning)

---

### Step 6: ID scheme violations

Check that all need IDs conform to the project's expected patterns.

**From pharaoh.toml**:
If `pharaoh.toml` defines `[pharaoh.id_scheme]` with a `pattern`, use that
pattern as the expected format. The pattern is a template string like
`"{TYPE}-{MODULE}-{NUMBER}"`. Convert it to a validation check:
- `{TYPE}` should match the need's type prefix.
- `{MODULE}` should be an uppercase alphanumeric string.
- `{NUMBER}` should be a zero-padded integer of at least `id_length` digits.

**From ubproject.toml**:
If no pharaoh.toml pattern exists, use the type prefixes from ubproject.toml.
Each need's ID should start with its type's `prefix` value (e.g., `REQ_` for
`req` type needs).

**Duplicate ID check**:
Scan all need IDs across all files. Report any ID that appears more than once.
Include the file paths and line numbers of each occurrence.

**ID format consistency**:
Even without an explicit pattern, check that all IDs of the same type follow a
consistent format. If most `req` IDs are `REQ_NNN` but one is `req-42`, flag
the outlier.

For each violation, record:
- Need ID
- Expected pattern
- Issue description
- File path and line number
- Severity (error for duplicates, warning for format issues)

---

### Step 7: Schema validation (if ubc CLI is available)

If the data access tier is ubc CLI (Tier 1):

1. Run `ubc schema validate` from the project root. Parse the output for
   validation errors and warnings.
2. Run `ubc check` from the project root. Parse the output for lint findings.
3. Include all results in the report under a dedicated section.
4. Merge any findings that overlap with Steps 2-6 to avoid duplicate reporting.
   If ubc reports the same gap or orphan that the file-based analysis found,
   keep only one entry and note the source.

If ubc CLI is not available, skip this step and note in the report:
```
Schema validation: Skipped (ubc CLI not available)
```

---

### Step 8: Present MECE report

Compile all findings into a single structured report. Use the format below
exactly. Omit sections that have no findings (but mention "None found" in the
summary counts).

```
## MECE Analysis Report

### Project
- Name: <project name>
- Data source: <tier>
- Needs analyzed: <total count>
- Types: <list>
- Required chains: <list of rules>

### Gaps (Missing Coverage)

| Source | Type | Missing | Required By |
|--------|------|---------|-------------|
| <id> | <type> | No <target_type> | <rule> |
| ... | ... | ... | ... |

### Orphans

| Need ID | Type | Title | Issue | Severity |
|---------|------|-------|-------|----------|
| <id> | <type> | <title> | <description> | error/warning/info |
| ... | ... | ... | ... | ... |

### Potential Redundancies

| Need A | Need B | Similarity | Reason |
|--------|--------|------------|--------|
| <id> | <id> | Title/Content/Structural | <brief reason> |
| ... | ... | ... | ... |

### Status Inconsistencies

| Need ID | Status | Issue | Severity |
|---------|--------|-------|----------|
| <id> | <status> | <description> | warning |
| ... | ... | ... | ... |

### ID Violations

| Need ID | Expected Pattern | Issue | Severity |
|---------|-----------------|-------|----------|
| <id> | <pattern> | <description> | error/warning |
| ... | ... | ... | ... |

### Schema Validation

<ubc results or "Skipped (ubc CLI not available)">

### Summary

- Gaps found: <N> (errors)
- Orphans: <N> (<X> errors, <Y> warnings, <Z> info)
- Redundancies: <N> (info)
- Status issues: <N> (warnings)
- ID violations: <N> (<X> errors, <Y> warnings)
- Schema issues: <N or "skipped">
- Overall health: <good / needs-attention / critical>
```

**Overall health classification**:

- **good**: Zero errors across all categories. Warnings and info items are
  acceptable.
- **needs-attention**: One or more errors exist, but total error count is 5 or
  fewer. The project has issues that should be addressed but is not
  fundamentally broken.
- **critical**: More than 5 errors, or any category has more errors than valid
  needs of that type. The traceability structure has significant problems.

---

### Step 9: Update session state

After presenting the report, update the session state file
(`.pharaoh/session.json`) as described in `skills/shared/strictness.md`:

1. Read the current `.pharaoh/session.json` (or create the default structure
   if it does not exist).
2. Set `global.mece_checked` to `true`.
3. Set `global.mece_timestamp` to the current ISO 8601 timestamp.
4. Set `updated` to the current ISO 8601 timestamp.
5. Write the file back.

This records that MECE analysis was performed, which satisfies the
`require_mece_on_release` gate if `pharaoh.toml` has it enabled.

---

## 3. Strictness Behavior

Follow the instructions in `skills/shared/strictness.md` for all strictness
decisions.

### pharaoh:mece has no prerequisites

This skill has no gates. It executes freely in both advisory and enforcing
mode. There is no prerequisite skill that must run before MECE analysis.

### pharaoh:mece as a prerequisite for others

When `pharaoh.toml` contains:

```toml
[pharaoh.workflow]
require_mece_on_release = true
```

then `pharaoh:release` requires a passing MECE check before it can proceed
(in enforcing mode). The session state field `global.mece_checked` must be
`true`.

In advisory mode, if `require_mece_on_release = true` and MECE has not been
run, `pharaoh:release` shows:

```
Tip: Consider running pharaoh:mece to check for gaps before release.
```

### Re-running after changes

If the user modifies needs after a MECE check, the session state is NOT
automatically invalidated. The recorded `mece_checked = true` persists until
the session is reset. This is by design -- the user decides when to re-run.

If you observe that needs were modified since the last MECE timestamp (by
comparing file modification times to `global.mece_timestamp`), mention this
in your output:

```
Note: Needs files were modified after the last MECE check
(<timestamp>). Consider re-running pharaoh:mece for an up-to-date analysis.
```

---

## 4. Scope Options

The user may request a scoped analysis instead of a full project scan. Support
the following scope modifiers. If no scope is specified, default to full project
analysis.

### Full project (default)

Analyze all needs across all files in all detected project roots. This is the
default when the user invokes `pharaoh:mece` with no arguments.

### Single file or directory

When the user specifies a file path or directory:

- Restrict the needs index to needs found in the specified file or directory.
- Still load the **full** link graph (all needs) so that link targets outside
  the scope can be resolved. A need in `auth/requirements.rst` may link to a
  need in `shared/types.rst` -- that link must still be validated.
- Report only findings for needs within the scope. Do not report issues for
  needs outside the scope, even if they are linked to scoped needs.
- Note the scope in the report header:
  ```
  Scope: auth/requirements.rst (12 of 47 needs)
  ```

### Specific need type

When the user specifies a type (e.g., "check only specs" or "mece for
requirements"):

- Restrict analysis to needs of the specified type.
- Gap analysis: Only check rules where the specified type is the source type.
- Orphan detection: Only report orphans of the specified type.
- Redundancy analysis: Only compare needs of the specified type (this is
  already the default behavior since redundancy only checks within a type).
- Status checks and ID checks: Only for the specified type.
- Note the scope in the report header:
  ```
  Scope: type=spec (15 of 47 needs)
  ```

### Specific traceability level

When the user specifies a level of the chain (e.g., "check the spec -> impl
link" or "mece for the implementation level"):

- Run gap analysis only for the specified rule or rules involving the
  specified type.
- Run orphan detection for types involved in the specified rule.
- Skip redundancy analysis, status checks, and ID checks (these are
  type-level concerns, not chain-level).
- Note the scope in the report header:
  ```
  Scope: chain spec -> impl (15 specs, 22 impls)
  ```

### Combining scopes

Scopes can be combined. For example, "check specs in auth/" applies both the
type filter and the directory filter. Apply all filters as a logical AND --
a need must match all specified criteria to be in scope.

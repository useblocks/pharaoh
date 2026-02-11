---
name: pharaoh-release
description: "Use when preparing a release, generating changelogs from requirements, or summarizing requirement changes for version management"
---

# pharaoh-release

Generate release artifacts from sphinx-needs changes. This skill identifies which
requirements, specifications, implementations, and test cases changed between
releases, produces structured changelogs and release notes, and computes
traceability coverage metrics suitable for safety-critical audit trails. In
enforcing mode, release is gated by prior verification (and optionally MECE
analysis).

## When to Use

- Preparing a release and need a changelog of requirement-level changes.
- Summarizing what needs were added, modified, or removed since the last release or tag.
- Producing traceability coverage metrics for compliance or audit documentation.
- Generating release notes that include requirement impact chains.

## Prerequisites

This skill has workflow gates. Follow the strictness check in Step 1 before
proceeding to the release process.

---

## Process

Execute the following steps in order.

---

### Step 1: Strictness Check

Follow the decision flow defined in `skills/shared/strictness.md`, Section 5.

#### 1a. Read strictness configuration

1. Look for `pharaoh.toml` in the workspace root.
2. Read `[pharaoh]` to determine the `strictness` level (`"advisory"` or `"enforcing"`).
3. Read `[pharaoh.workflow]` for the gate settings:
   - `require_verification` (default: `true`)
   - `require_mece_on_release` (default: `false`)
4. If `pharaoh.toml` does not exist, treat strictness as `"advisory"`.

#### 1b. Advisory mode

If `strictness = "advisory"`:

- Proceed directly to Step 2 without blocking.
- After the release output is complete (Step 6), check whether prerequisites were
  skipped and show relevant tips (at most one per missing prerequisite):

| Missing prerequisite | Tip |
|---|---|
| `pharaoh:verify` not run | `Tip: Consider running pharaoh:verify to validate implementations before release.` |
| `pharaoh:mece` not run | `Tip: Consider running pharaoh:mece to check for gaps before release.` |

Do not show a tip if the corresponding workflow gate is disabled in `pharaoh.toml`
(e.g., do not show the MECE tip if `require_mece_on_release = false`).

#### 1c. Enforcing mode

If `strictness = "enforcing"`:

1. Read `.pharaoh/session.json` (see `skills/shared/strictness.md`, Section 4).
2. Check **verification gate** (if `require_verification = true`):
   - Look at the `changes` dictionary in session state.
   - Every need that was authored or modified in this session must have `verified = true`.
   - If any need has `verified = false` or is missing from session state, block:
     ```
     Blocked: Verification required before release.
     Run pharaoh:verify to validate implementations first.

     Unverified needs:
       - REQ_001 (authored but not verified)
       - SPEC_003 (authored but not verified)
     ```
3. Check **MECE gate** (if `require_mece_on_release = true`):
   - Check `global.mece_checked` in session state.
   - If `mece_checked = false` or `null`, block:
     ```
     Blocked: MECE analysis required before release.
     Run pharaoh:mece to check for gaps first.
     ```
4. If any gate fails, stop. Do not proceed to Step 2.
5. If all gates pass, proceed to Step 2.

#### 1d. User bypass

If the user explicitly requests to skip a gate check (e.g., "proceed anyway" or
"skip the check"), respect the request. Log a warning:

```
Warning: Skipping verification gate at user request. Workflow compliance is not guaranteed.
```

Proceed with Step 2. Do not update session state to indicate the prerequisite was met.

---

### Step 2: Get Project Data

Follow the instructions in `skills/shared/data-access.md` to:

1. Detect the project structure (find `ubproject.toml`, `conf.py`, source directories).
2. Read the project configuration (need types, extra_links, ID settings).
3. Determine the data access tier (ubc CLI > ubCode MCP > raw file parsing).
4. Build the needs index with all needs and their attributes.
5. Build the link graph with all relationships in both directions.
6. Detect sphinx-codelinks configuration.
7. Read `pharaoh.toml` for traceability requirements (`required_links`).

After completing data access, present the detection summary before proceeding:

```
Project: <name> (<config source>)
Types: <list of directive names>
Links: <list of link type names>
Data source: <tier used>
Needs found: <count>
Strictness: <advisory|enforcing>
```

If detection fails (no project found, no needs in source files), report the issue
and ask the user for guidance. Do not proceed with empty data.

---

### Step 3: Determine Release Scope

Identify which version this release covers and what to compare against.

#### 3a. Get version identifier from user

Ask the user for the release version if not already provided:

```
What version is this release?
  - Enter a version string (e.g., v1.2.0)
  - Or type "since last release" to auto-detect from the latest git tag
```

If the user provides a version string, record it as the release version.

#### 3b. Find the comparison baseline

Determine the baseline to compare against:

**If the user said "since last release" or provided no baseline:**

1. Run `git tag --sort=-v:refname` to list tags in reverse version order.
2. Take the most recent tag as the baseline.
3. If no tags exist, use the initial commit as the baseline.
4. Confirm with the user:
   ```
   Comparing against: <tag> (<date>)
   Proceed? [yes/no]
   ```

**If the user provided a specific baseline** (a tag, branch, or commit):

1. Verify the reference exists with `git rev-parse <ref>`.
2. If it does not exist, report the error and ask for a valid reference.

#### 3c. Determine changed files

Use git to find which documentation files changed between the baseline and HEAD:

```
git diff --name-only <baseline>..HEAD -- <source_directories>
```

Filter to only RST and MD files (the files that can contain need directives).
Record the list of changed files.

If `ubc diff` is available (the ubc CLI was detected and supports the `diff`
subcommand), prefer it for structural diff:

```
ubc diff <baseline>..HEAD --format json
```

This provides a precise need-level diff rather than file-level, which is more
accurate for detecting added, modified, and removed needs.

---

### Step 4: Identify Changed Needs

Categorize every need change into one of three buckets: new, modified, or removed.

#### 4a. Using ubc diff (Tier 1)

If `ubc diff` is available and returned JSON output in Step 3c, parse it directly.
The output provides need-level changes with before/after states. Map each entry to
the appropriate bucket.

#### 4b. Using git diff with raw parsing (fallback)

If `ubc diff` is not available, analyze changes manually:

**Find new needs:**

1. For each changed file, run `git diff <baseline>..HEAD -- <file>`.
2. In the diff output, look for added lines (prefixed with `+`) that contain
   need directives: `.. <type>::` where `<type>` is one of the configured
   directive names.
3. For each added directive, parse the full need (title, ID, options) from the
   current version of the file.
4. Record as a new need.

**Find removed needs:**

1. In the diff output, look for removed lines (prefixed with `-`) that contain
   need directives.
2. Parse the full need from the old version (use `git show <baseline>:<file>`
   to read the old content).
3. Verify the need ID no longer exists in the current needs index.
4. Record as a removed need.

**Find modified needs:**

1. For each need ID that appears in both the baseline and current versions of
   changed files, compare the need's attributes:
   - Title changed
   - Status changed
   - Content/body changed
   - Options changed (tags, links, custom options)
   - Link targets changed
2. For each attribute that differs, record the old and new values.
3. Record as a modified need with a list of changed attributes.

#### 4c. Build the change summary

Organize all changes into a structured summary:

```
Changes detected:
  New needs:      <count> (<breakdown by type>)
  Modified needs: <count> (<breakdown by type>)
  Removed needs:  <count> (<breakdown by type>)
  Unchanged:      <count>
```

For each modified need, also identify its **impact chain**: the set of needs
linked to it (upstream and downstream) that may be affected by the change. Use the
link graph built in Step 2 to trace one level in each direction.

---

### Step 5: Generate Changelog

Build a structured changelog from the change summary.

#### 5a. Changelog format

Use the following markdown template. Group changes by need type. Within each
group, sort by need ID.

```markdown
## Release <version> - <date>

### Summary

- **<count>** new needs added
- **<count>** needs modified
- **<count>** needs removed
- **<total>** total needs in project

### New Requirements
- **REQ_004**: <title> [<status>]
  <brief description or first sentence of content>

### New Specifications
- **SPEC_005**: <title> [<status>]
  Linked to: REQ_004

### New Implementations
- (none)

### New Test Cases
- (none)

### Modified Requirements
- **REQ_001**: <title>
  - <attribute>: <old value> -> <new value>
  - Impact: <list of directly linked need IDs that may need review>

### Modified Specifications
- **SPEC_001**: <title>
  - content: updated acceptance criteria
  - Impact: IMPL_001, TEST_001

### Modified Implementations
- (none)

### Modified Test Cases
- (none)

### Removed Requirements
- (none)

### Removed Specifications
- (none)

### Removed Implementations
- (none)

### Removed Test Cases
- (none)

### Traceability Changes
- New links: <list of new link pairs, e.g., SPEC_005 -> REQ_004>
- Removed links: <list of removed link pairs>
- Modified links: <list of needs whose link targets changed>

### Verification Status
- All modified needs verified: <yes/no>
- Unverified needs: <list of IDs, or "none">
- MECE analysis: <passed / not run>
- Open MECE issues: <count, or "N/A">
```

**Adapt the type sections to the project's configured types.** If the project
defines custom types beyond the standard four (e.g., `story`, `hazard`,
`constraint`), generate sections for each type that has changes. Omit type
sections that have no changes in any category (no new, no modified, no removed).

#### 5b. Changelog for custom need types

For each need type defined in the project configuration, generate the
corresponding "New", "Modified", and "Removed" sections only if that type has at
least one change. Use the type's `title` field from the configuration for the
section heading (e.g., "New Hazard Analyses" for a type with `title = "Hazard Analysis"`).

#### 5c. Verification status section

Populate the verification status from session state (`.pharaoh/session.json`):

- Check `changes.<need_id>.verified` for each modified or new need.
- Check `global.mece_checked` for MECE status.
- If session state does not exist, report:
  ```
  Verification Status
  - Session state not available. Run pharaoh:verify and pharaoh:mece for status.
  ```

---

### Step 6: Generate Release Summary

Produce a high-level summary with coverage metrics.

#### 6a. Needs inventory

Count all needs in the current project by type and status:

```
Needs Inventory
===============
Type            Total   draft   approved   implemented   verified
Requirement       12       2          5             3          2
Specification     10       1          4             3          2
Implementation     8       0          2             4          2
Test Case          7       0          1             3          3
--------------------------------------------------------------
Total             37       3         12            13          9
```

Adapt the status columns to the project's actual status values. If the project
uses different statuses (e.g., `open`, `in_progress`, `closed`), use those instead.

#### 6b. Traceability coverage metrics

Calculate coverage percentages based on `required_links` from `pharaoh.toml`:

For each required link chain (e.g., `"req -> spec"`):

1. Count the number of source-type needs (e.g., all `req` needs).
2. Count how many have at least one link to a target-type need (e.g., linked to
   at least one `spec`).
3. Calculate: `coverage = linked_count / total_count * 100`

Present as:

```
Traceability Coverage
=====================
Chain               Covered   Total   Coverage
req -> spec              10      12      83.3%
spec -> impl              8      10      80.0%
impl -> test              7       8      87.5%
Full chain (req->test)    6      12      50.0%
```

The "Full chain" row traces the complete path from top-level needs to leaf needs.
A source need is "fully covered" only if there is a complete path through all
intermediate types to the final type in the chain.

If `required_links` is not configured, skip this section and note:

```
Traceability coverage: Not configured.
Add [pharaoh.traceability] required_links to pharaoh.toml to enable coverage metrics.
```

#### 6c. Open issues from MECE analysis

If `pharaoh:mece` was run in this session (check `global.mece_checked` in session
state), summarize any open issues that were identified:

- Orphaned needs (needs with no incoming or outgoing links)
- Gaps in required link chains
- Redundant or overlapping needs
- Inconsistent statuses (e.g., a `verified` need linked to a `draft` specification)

If MECE was not run, note:

```
MECE Issues: Not available (pharaoh:mece has not been run this session).
```

#### 6d. Codelinks summary

If sphinx-codelinks is enabled, include a code traceability summary:

```
Code Traceability
=================
Needs with code references: <count> / <total>
Code files referencing needs: <count>
```

---

### Step 7: Output and Next Steps

#### 7a. Present changelog to user

Display the complete changelog (from Step 5) and release summary (from Step 6)
to the user in a single output.

#### 7b. Offer to write to file

After presenting the output, ask the user:

```
Would you like to save these release artifacts?

  1. Write changelog to CHANGELOG.md (append at top)
  2. Write full release notes to docs/releases/<version>.md
  3. Write both
  4. Do not write any files

Choose an option: [1/2/3/4]
```

**Option 1: Append to CHANGELOG.md**

1. Check if `CHANGELOG.md` exists in the workspace root.
2. If it exists, read its current content. Insert the new changelog entry at the
   top of the file, after any existing header (e.g., after a `# Changelog` line).
3. If it does not exist, create it with a `# Changelog` header followed by the
   new entry.
4. Show the user what will be written and confirm before writing.

**Option 2: Write to docs/releases/**

1. Create the `docs/releases/` directory if it does not exist.
2. Write the full release notes (changelog + release summary) to
   `docs/releases/<version>.md`.
3. Show the user what will be written and confirm before writing.

**Option 3: Both**

Execute both Option 1 and Option 2.

**Option 4: No files**

Do nothing. The output was already presented on screen.

#### 7c. Suggest git tag

After file output is handled, suggest tagging:

```
Suggested next step:
  git tag -a <version> -m "Release <version>"

Create this tag now? [yes/no]
```

If the user confirms, run the `git tag` command. Do **not** push the tag. If the
user wants to push, they must explicitly request it.

If the user declines, do nothing.

#### 7d. Update session state

After the release process completes successfully (regardless of whether files were
written), update `.pharaoh/session.json`:

1. Read the current session state (or create the initial structure).
2. Set `global.last_release` to the current ISO 8601 timestamp.
3. Set `updated` to the current ISO 8601 timestamp.
4. Write the updated JSON back to `.pharaoh/session.json`.

---

## Key Constraints

1. **Never auto-tag or auto-push without user confirmation.** The `git tag` and
   `git push` commands must always be explicitly confirmed by the user. Never run
   them silently.

2. **Never overwrite files without asking.** Before writing to `CHANGELOG.md` or
   any release notes file, show the user what will be written and get explicit
   confirmation. If the file already exists, show how it will be modified.

3. **Include traceability metrics for safety-critical audit trails.** The release
   summary must always include the needs inventory and traceability coverage
   metrics. These are essential for compliance in regulated industries (automotive,
   aerospace, medical device).

4. **Support both full release notes and incremental changelogs.** The changelog
   (Step 5) captures incremental changes for this release. The release summary
   (Step 6) captures the full project state. Both are produced every time.

5. **Adapt to project-specific types and statuses.** Do not hardcode need types
   (`req`, `spec`, `impl`, `test`) or status values (`draft`, `approved`). Read
   the project configuration and use whatever types and statuses the project
   defines. Generate changelog sections dynamically.

6. **Handle missing git history gracefully.** If the project is not a git
   repository, or if there are no tags, report the limitation:
   ```
   This workspace is not a git repository (or has no tags).
   Cannot determine changes since last release automatically.

   Please provide the set of changed need IDs manually, or specify two
   file snapshots to compare.
   ```
   Then allow the user to provide change information manually and proceed
   with changelog generation from that input.

7. **Handle empty releases.** If no needs changed between the baseline and HEAD,
   report:
   ```
   No requirement changes detected between <baseline> and HEAD.

   If documentation files changed but no need directives were affected,
   this is a documentation-only release with no requirements impact.
   ```
   Still offer to generate the release summary (Step 6) since the project
   inventory and coverage metrics may be useful even without changes.

8. **Respect the data access tier hierarchy.** Always prefer ubc CLI (`ubc diff`)
   for change detection when available. Fall back to git diff with raw parsing
   only when ubc is not available. The structural diff from ubc is more precise
   than text-based diff parsing.

9. **Do not modify any need directives.** This skill is read-only with respect to
   documentation source files. It generates release artifacts and writes them to
   dedicated output files (CHANGELOG.md, docs/releases/). It never modifies RST
   or MD files containing need directives.

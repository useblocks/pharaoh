---
description: Prepare a release by generating changelogs from requirements, release summaries, and traceability coverage metrics.
handoffs:
  - label: MECE Check
    agent: pharaoh.mece
    prompt: Run MECE analysis before release
---

# @pharaoh.release

Generate release artifacts from sphinx-needs changes. Identifies which needs changed between releases, produces structured changelogs and release notes, and computes traceability coverage metrics for audit trails.

## Strictness Check

**Enforcing mode**:
1. If `require_verification = true`: Check `.pharaoh/session.json` for `verified = true` on all authored/modified needs. Block if any are unverified.
2. If `require_mece_on_release = true`: Check `global.mece_checked = true`. Block if MECE not run.

**Advisory mode**: Proceed freely. Show tips for missing prerequisites after output.

**User bypass**: If user says "proceed anyway", allow with a warning.

## Data Access

1. **ubc CLI**: `ubc build needs --format json`, `ubc diff` for structural change detection.
2. **ubCode MCP**: Pre-indexed data.
3. **Raw file parsing**: Config from `ubproject.toml`/`conf.py`. Git diff for change detection.

## Process

### Step 1: Get Project Data

Build needs index and link graph. Present detection summary.

### Step 2: Determine Release Scope

- Get version identifier from user (or "since last release").
- Find comparison baseline: latest git tag (`git tag --sort=-v:refname`), or user-specified ref.
- Find changed files: `git diff --name-only <baseline>..HEAD -- <source_dirs>` (or `ubc diff` if available).

### Step 3: Identify Changed Needs

Categorize into: **new**, **modified**, **removed**.

- **With ubc diff** (Tier 1): Parse JSON output for need-level changes.
- **With git diff** (fallback): Look for added/removed directive lines, compare attributes between baseline and current.

Build change summary with type breakdowns and impact chains.

### Step 4: Generate Changelog

```markdown
## Release <version> - <date>

### Summary
- **<count>** new needs added
- **<count>** needs modified
- **<count>** needs removed

### New <Type>s
- **<ID>**: <title> [<status>]

### Modified <Type>s
- **<ID>**: <title>
  - <attribute>: <old> -> <new>
  - Impact: <linked IDs that may need review>

### Removed <Type>s
- **<ID>**: <title>

### Traceability Changes
- New links: <list>
- Removed links: <list>

### Verification Status
- All modified needs verified: <yes/no>
- MECE analysis: <passed / not run>
```

Adapt sections dynamically to the project's configured types. Omit empty sections.

### Step 5: Generate Release Summary

**Needs inventory**: Count all needs by type and status.

**Traceability coverage**: For each `required_links` rule, calculate `coverage = linked / total * 100%`. Include full-chain coverage.

**MECE issues**: Summarize open issues from session state if available.

**Codelinks summary**: If enabled, count needs with code references.

### Step 6: Output and Next Steps

1. Present changelog and release summary.
2. Offer to write files:
   - Append to `CHANGELOG.md`
   - Write to `docs/releases/<version>.md`
   - Both, or neither
3. Suggest git tag: `git tag -a <version> -m "Release <version>"`. Only create if user confirms. Never push.
4. Update session state: set `global.last_release` to current timestamp.

## Constraints

1. Never auto-tag or auto-push without user confirmation.
2. Never overwrite files without asking.
3. Always include traceability metrics for audit trails.
4. Adapt to project-specific types and statuses. Don't hardcode.
5. Handle missing git history gracefully.
6. Never modify need directive source files. This agent is read-only for documentation.
7. Prefer `ubc diff` when available for accurate structural change detection.

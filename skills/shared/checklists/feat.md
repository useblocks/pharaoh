---
name: feat
applies_to: feat
axes:
  - trace_to_parent_or_workflow
  - single_user_capability
  - source_doc_present_and_valid
  - required_fields_complete
  - shall_clause_user_observable
  - body_length_within_bounds
  - no_comp_level_mechanism_leak
  - naming_clarity
---

# Feat review checklist

Generic baseline for reviewing feat-level needs. Project-specific addenda in `.pharaoh/project/checklists/feat.md` extend but never replace these.

## Mechanized axes (pass/fail, execution-based reward)

### trace_to_parent_or_workflow

**Check:** The feat has `:satisfies:` or `:realizes:` linking to a parent workflow (`wf__*`), a higher-level feat, or a stakeholder need. An orphan feat (no parent link) fails.

**Detection rule:** In the feat directive, grep for any outgoing link option declared in `artefact-catalog.yaml` under the feat type. At least one must resolve.

### source_doc_present_and_valid

**Check:** The feat has a `:source_doc:` field, and the referenced path exists in the repository.

**Detection rule:** Read `:source_doc:` value; assert file exists relative to the docs root.

### required_fields_complete

**Check:** All fields listed under `artefact-catalog.yaml > feat > required_fields` are present in the directive options.

**Detection rule:** Parse directive options; diff against required_fields list.

### body_length_within_bounds

**Check:** The feat body (prose + shall-clauses) is between 3 and 15 non-blank lines. Shorter = under-specified. Longer = likely two feats fused.

**Detection rule:** Count non-blank lines between the directive header and the next RST section or directive.

## Subjective axes (0-3 score, LLM-judge fallback)

### single_user_capability (0-3)

**Rubric:**
- 3 — Describes exactly one user-facing capability. Name and body refer to one action, one data flow, one exit.
- 2 — One capability with minor overlap into a neighbour (e.g. "export and notify").
- 1 — Two or more capabilities fused (e.g. "reqif_exchange" covers both export and import).
- 0 — Capability not identifiable; body describes implementation rather than behavior.

### shall_clause_user_observable (0-3)

**Rubric:**
- 3 — Shall-clause expresses observable external behavior: input X → output Y, no internal mechanism named.
- 2 — Minor mechanism reference that does not obscure the external behavior.
- 1 — Shall-clause names an internal module, class, or function and the user-observable behavior is unclear.
- 0 — Shall-clause is implementation description, not a behavioral claim.

### no_comp_level_mechanism_leak (0-3)

**Rubric:**
- 3 — Body contains no references to specific classes, methods, file paths, or data structures. Pure user / system / external-interface vocabulary.
- 2 — One or two stray references that do not dominate.
- 1 — Body half-describes mechanism (e.g. "the JamaClient fetches items and the Jama2Needs processor converts...").
- 0 — Body reads like a method-level docstring.

### naming_clarity (0-3)

**Rubric:**
- 3 — ID and title are self-explanatory to a reviewer unfamiliar with the codebase.
- 2 — Mostly clear, one abbreviation or acronym without expansion.
- 1 — Opaque abbreviations dominate; title does not disambiguate siblings.
- 0 — Generic placeholder names (`FEAT_stuff`, `FEAT_misc`).

## Tailoring extension point

Per-project addenda under `.pharaoh/project/checklists/feat.md` add axes with keys prefixed `tailoring.*`. Examples:

- Safety-critical project: `tailoring.asil_marker_present` (every feat carries the project's safety-classification marker).
- Connector project: `tailoring.connector_family_named` (every connector feat names its family per the project's controlled vocabulary).

Extension axes follow the same mechanized vs subjective split. The base axes are always run; tailoring axes are run only if the project defines them.

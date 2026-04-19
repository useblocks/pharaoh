# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Removed

- **pharaoh-author** -- monolithic requirement-authoring skill, replaced by the atomic chain below.
- **pharaoh-verify** -- monolithic requirement-review skill, replaced by the atomic chain below.

  Empirical justification: Phase-1 pilot (pharaoh-validation `runs/phase1-*/FINDINGS.md`) and Phase-2 mini-pilot (pharaoh-validation `runs/phase2-1776446795/FINDINGS.md`) showed the atomic chain achieves A_exec 0.79 vs 0.15 for the monolith (+0.641 delta).

### Added

Atomic-skill chain (16 new skills) replacing the retired monolith pair:

- **pharaoh-arch-draft** -- Draft a single architecture element directive from a parent requirement.
- **pharaoh-arch-review** -- Audit an architecture element against ISO 26262-8 §6 axes.
- **pharaoh-coverage-gap** -- Detect one gap category (orphan / unverified / duplicate / ...) in a corpus.
- **pharaoh-flow** -- Orchestrate the full V-model chain (req → arch → vplan → fmea) for one feature context.
- **pharaoh-fmea** -- Derive a single failure-mode entry (FMEA/DFA row) from a requirement or architecture element.
- **pharaoh-lifecycle-check** -- Verify artefact lifecycle state and legality of a state transition.
- **pharaoh-process-audit** -- Full-corpus audit orchestrating pharaoh-coverage-gap across all gap categories.
- **pharaoh-req-draft** -- Draft a single requirement directive (replaces authoring half of pharaoh-author).
- **pharaoh-req-regenerate** -- Regenerate a requirement to address findings from pharaoh-req-review.
- **pharaoh-req-review** -- Audit a requirement against ISO 26262-8 §6 axes (replaces review half of pharaoh-verify).
- **pharaoh-standard-conformance** -- Evaluate a single artefact against a regulatory standard (ISO 26262-8, ASPICE 4.0, ISO/SAE 21434).
- **pharaoh-tailor-detect** -- Inspect a project and emit detected conventions for tailoring.
- **pharaoh-tailor-fill** -- Author `.pharaoh/project/` tailoring files from detected conventions.
- **pharaoh-tailor-review** -- Audit tailoring files against schemas and cross-file consistency.
- **pharaoh-vplan-draft** -- Draft a single test-case directive linking to a parent requirement.
- **pharaoh-vplan-review** -- Audit a test case against ISO 26262-8 §6 axes plus vplan-specific axes.

## [0.1.0] - 2026-04-10

### Added

- **Skills (Claude Code):** pharaoh:setup, pharaoh:change, pharaoh:trace, pharaoh:mece, pharaoh:author, pharaoh:verify, pharaoh:release, pharaoh:plan, pharaoh:spec, pharaoh:decide
- **Agents (GitHub Copilot):** matching agents for all skills with handoff support
- **Prompts (GitHub Copilot):** quick-invoke prompts for common workflows
- **Shared modules:** data-access (3-tier detection) and strictness (advisory/enforcing mode)
- **Test fixtures:** basic-project with requirements, specifications, implementations, tests, and decisions
- **Configuration:** pharaoh.toml.example with all supported options
- **Subagent:** sphinx-needs-expert for deep sphinx-needs domain knowledge

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-04-10

### Added

- **Skills (Claude Code):** pharaoh:setup, pharaoh:change, pharaoh:trace, pharaoh:mece, pharaoh:author, pharaoh:verify, pharaoh:release, pharaoh:plan, pharaoh:spec, pharaoh:decide
- **Agents (GitHub Copilot):** matching agents for all skills with handoff support
- **Prompts (GitHub Copilot):** quick-invoke prompts for common workflows
- **Shared modules:** data-access (3-tier detection) and strictness (advisory/enforcing mode)
- **Test fixtures:** basic-project with requirements, specifications, implementations, tests, and decisions
- **Configuration:** pharaoh.toml.example with all supported options
- **Subagent:** sphinx-needs-expert for deep sphinx-needs domain knowledge

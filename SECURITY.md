# Security Policy

## About Pharaoh's Architecture

Pharaoh is a **pure-prompt project**. It contains no executable code, no compiled binaries, and no runtime dependencies. All logic is encoded in markdown instruction files that are interpreted by AI assistants (Claude Code, GitHub Copilot).

This means Pharaoh's attack surface is fundamentally different from traditional software.

## What Counts as a Security Issue

- Skill or agent instructions that could cause an AI to **delete files, leak secrets, or execute destructive commands**
- **Prompt injection vectors** in skill files that could override user intent
- Instructions that cause an AI to **bypass safety checks** or ignore user permissions
- Skill logic that could **exfiltrate data** from a user's project to external services

## What Does NOT Count

- Bugs in AI output quality (e.g., incorrect traceability analysis)
- sphinx-needs configuration issues
- Unexpected AI behavior not caused by Pharaoh's instructions

## Reporting a Vulnerability

**Email:** security@useblocks.com

Include:
- Which skill or agent file is affected
- A description of the vulnerability
- Steps to reproduce (if possible)

**Response time:** We will acknowledge your report within **5 business days**.

## Disclosure Policy

- We will work with you to understand and validate the issue
- Fixes ship as prompt updates (updated skill/agent files) — there are no versioned binaries to patch
- We will credit reporters in the changelog unless they prefer to remain anonymous

## No CVEs

Pure-prompt projects do not have CVE identifiers. Security fixes are tracked in git history and the changelog.

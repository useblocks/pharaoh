# Contributing to Pharaoh

Pharaoh is maintained by [useblocks](https://useblocks.com) and welcomes contributions from the community. This guide covers how the project is structured, how to make changes, and how to submit contributions.

## Project Structure

```
pharaoh/
  skills/                          # Claude Code skills (SKILL.md files)
    shared/                        # Shared instructions referenced by all skills
      data-access.md               # Three-tier data access pattern
      strictness.md                # Advisory/enforcing mode logic
    pharaoh-setup/SKILL.md
    pharaoh-change/SKILL.md
    pharaoh-trace/SKILL.md
    pharaoh-mece/SKILL.md
    pharaoh-author/SKILL.md
    pharaoh-verify/SKILL.md
    pharaoh-release/SKILL.md
    pharaoh-plan/SKILL.md
  agents/                          # Claude Code subagent definitions
    sphinx-needs-expert/agent.md
  copilot/                         # GitHub Copilot integration
    agents/                        # Copilot agent files (.agent.md)
    prompts/                       # Copilot prompt files (.prompt.md)
    copilot-instructions.md        # General Copilot context
  tests/
    fixtures/                      # Sample sphinx-needs projects for testing
  .claude-plugin/                  # Claude Code plugin manifests
  docs/plans/                      # Design documents
```

### Key Concept: Pure Prompt Architecture

Pharaoh has **no runtime binary or Python package**. All analysis logic is encoded in markdown instruction files. The AI (Claude, Copilot) is the runtime. This means:

- Adding a feature = editing or creating a markdown file
- Testing = invoking the skill against a fixture project and verifying the output
- Bug fixes = adjusting the instructions in the relevant SKILL.md or agent.md

## How to Contribute

### Improving an Existing Skill

1. Read the skill file in `skills/<name>/SKILL.md`.
2. Read `skills/shared/data-access.md` and `skills/shared/strictness.md` -- most skills reference these.
3. Make your changes. Follow the existing structure and conventions in the file.
4. Test manually by invoking the skill against `tests/fixtures/basic-project/`.
5. If the skill has a Copilot counterpart in `copilot/agents/`, update that file to match.

### Adding a New Skill

1. Create `skills/<name>/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: pharaoh-<name>
   description: "Use when <trigger condition>"
   ---
   ```
2. The `name` field must use only lowercase letters, numbers, and hyphens.
3. The `description` must start with "Use when".
4. Include data access instructions (reference `skills/shared/data-access.md`).
5. Include strictness handling (reference `skills/shared/strictness.md`).
6. Add a corresponding Copilot agent in `copilot/agents/pharaoh.<name>.agent.md` with handoffs.
7. Add a prompt file in `copilot/prompts/pharaoh.<name>.prompt.md`.
8. Update the skills table in `README.md`.
9. Update `copilot/copilot-instructions.md` with the new agent.

### Updating Shared Instructions

Changes to `skills/shared/data-access.md` or `skills/shared/strictness.md` affect all skills. Be especially careful:

- Test changes against multiple skills, not just one.
- Copilot agents inline their data access logic (they don't reference the shared files). If you change shared instructions, update the Copilot agents to match.

### Adding Test Fixtures

Test fixtures live in `tests/fixtures/`. Each fixture is a minimal sphinx-needs project. To add one:

1. Create a directory under `tests/fixtures/` with a descriptive name.
2. Include at minimum: `ubproject.toml` (or `conf.py`) and at least one RST file with need directives.
3. Document what the fixture is designed to test (e.g., multi-project setup, custom link types, codelinks).

## Coding Conventions

### Skill Files

- Use markdown with clear step-by-step instructions.
- Number steps sequentially. Use sub-steps (e.g., Step 3a, Step 3b).
- Include the data access detection summary format in every skill that reads project data.
- Include concrete examples showing expected input and output.
- Specify exact output formats (use code blocks with the template).
- State constraints at the end of the file.

### Copilot Agents

- Mirror the corresponding Claude Code skill's logic.
- Include YAML frontmatter with `description` and `handoffs`.
- Inline data access instructions (Copilot agents can't reference shared files).
- Keep them self-contained but more concise than the Claude Code skills.

### Commit Messages

- Use imperative mood: "Add feature" not "Added feature".
- First line: brief summary (under 72 characters).
- Group related changes in a single commit.

## Developer Certificate of Origin

This project uses the [Developer Certificate of Origin](https://developercertificate.org/) (DCO). By contributing, you certify that you wrote or have the right to submit the code under the project's MIT license.

Sign off your commits with:

```bash
git commit -s -m "Your commit message"
```

All commits in a PR must be signed off. If you forget, you can amend:

```bash
git commit --amend -s
```

## Pull Request Process

1. Fork the repository and create a branch from `main`.
2. Make your changes following the conventions above.
3. Test your changes manually against the test fixtures.
4. Ensure both the Claude Code skill and Copilot agent are updated if applicable.
5. Submit a pull request with:
   - A clear description of what changed and why.
   - Which skills/agents were modified.
   - How you tested the changes.

## Reporting Issues

Use the GitHub issue templates:

- **[Bug Report](?template=bug_report.md)** -- for problems with skills or agents
- **[Feature Request](?template=feature_request.md)** -- for improvements or new capabilities

The templates include fields for the skill/agent involved, AI platform, and project configuration.

## Questions?

Open a GitHub issue for questions about contributing. We're happy to help.

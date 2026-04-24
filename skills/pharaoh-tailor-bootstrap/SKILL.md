---
name: pharaoh-tailor-bootstrap
description: Use when a sphinx-needs project has just been bootstrapped (post pharaoh-bootstrap, pre any needs authoring) and you need to generate minimal tailoring files from declared types — workflows.yaml, id-conventions.yaml, artefact-catalog.yaml, and per-type checklists — without requiring any needs to exist. Complements pharaoh-tailor-detect which requires ≥10 needs.
---

# pharaoh-tailor-bootstrap

## When to use

Invoke immediately after `pharaoh-bootstrap` + `pharaoh-setup` on a greenfield sphinx-needs project. The project has declared need types in `ubproject.toml` but has zero needs yet, so `pharaoh-tailor-detect` (which requires ≥10 needs to infer conventions) fails by design. This skill fills the "tailoring donut hole" — it emits minimal but valid tailoring derived from the bootstrap inputs, so:

- Every need gets a defined lifecycle (`:status: draft` can transition to `reviewed` and `approved`).
- ID patterns are machine-checkable before the first need lands.
- `pharaoh-quality-gate` has a gate spec to evaluate against.
- Review checklists exist per type for `pharaoh-req-review` to consume.

Do NOT use on a project that already has `.pharaoh/project/*.yaml` files — this skill never overwrites without explicit `overwrite=true`. Run `pharaoh-tailor-detect` / `pharaoh-tailor-fill` on matured projects instead.

## Atomicity

- (a) Indivisible — one `project_root` in → up to 5 files out in `.pharaoh/project/`. No needs authoring, no RST mutation, no setup-level edits. One tailoring phase × one project.
- (b) Input: `{project_root: str, overwrite?: bool}`. Output: JSON `{files_created: list[str], files_skipped: list[str], warnings: list[str]}`. Default `overwrite=false`.
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-tailor-bootstrap/input_ubproject.toml` declares two types (`feat` FEAT_, `comp_req` CREQ_) and one extra_link (`satisfies`). Run skill against it. Scorer checks:
  1. Five files created under `.pharaoh/project/`: `workflows.yaml`, `id-conventions.yaml`, `artefact-catalog.yaml`, `checklists/feat.md`, `checklists/comp_req.md`.
  2. Each emitted file's content matches the corresponding `expected_output/` fixture byte-exact (YAML canonical-sorted for the YAML files; md exact for the checklists).
  3. Re-running the skill with `overwrite=false` on the now-populated `.pharaoh/project/` is idempotent: `files_created=[]`, `files_skipped` lists all five, `warnings=[]`.
  4. Running with `overwrite=true` on populated target regenerates all five (byte-exact equality with fixture preserved).

  Pass = all 4 checks.
- (d) Reusable on any first-time Pharaoh project.
- (e) Composable: callable by `pharaoh-setup` post-bootstrap. Never calls other skills.

## Input

- `project_root`: absolute path. Must contain `ubproject.toml` with at least one `[[needs.types]]` entry.
- `overwrite` (optional): if `true`, regenerate existing tailoring files. Default `false` (skip + warn on collision).

## Output

```json
{
  "files_created": [
    ".pharaoh/project/workflows.yaml",
    ".pharaoh/project/id-conventions.yaml",
    ".pharaoh/project/artefact-catalog.yaml",
    ".pharaoh/project/checklists/feat.md",
    ".pharaoh/project/checklists/comp_req.md",
    ".pharaoh/project/checklists/requirement.md"
  ],
  "files_skipped": [],
  "warnings": []
}
```

Paths are relative to `project_root`.

## Process

### Step 1: Read ubproject.toml

Read `<project_root>/ubproject.toml`. Extract every `[[needs.types]]` entry's `directive` and `prefix`. Extract every `[[needs.extra_links]]` entry's `option`, `incoming`, `outgoing`.

If zero types declared, FAIL: `"no [[needs.types]] in ubproject.toml; run pharaoh-bootstrap first"`.

### Step 2: Emit workflows.yaml

For each declared type, emit a block with states `draft`, `reviewed`, `approved`, transitions `draft→reviewed` (gate `reviewer_present`), `reviewed→approved` (gate `approver_present`), `reviewed→draft` (gate `reviewer_rejected`), initial `draft`, final `approved`.

See `expected_output/workflows.yaml` in the fixture for exact format.

### Step 3: Emit id-conventions.yaml

`prefixes`: mapping from each directive to its prefix. `id_regex`: OR-join of all prefixes as a regex anchored to start + snake_case tail. `separator`: `"_"`.

See fixture for exact format.

### Step 4: Emit artefact-catalog.yaml

For each declared type, emit:
- `required_fields`: at minimum `id`, `status`.
- `optional_fields`: `reviewer`, `approved_by`, plus `source_doc` for types that typically carry provenance (heuristic: top-level types like `feat`, `story`, `use_case` — if unsure, include it).
- `child_of`: list of parent types inferred from extra_links. Rule: if `satisfies` link exists, types that commonly use it (`comp_req`, `spec`, `impl`) list their parent (`feat`, `story`, etc.). If no clear inference, `child_of: []` — caller tunes later.
- `lifecycle_ref`: `workflows.yaml#<type>`.

### Step 5: Emit per-type checklists

For each declared type, write `checklists/<directive>.md` with frontmatter `applies_to: <directive>`, `required_before: [reviewed]`, and a short review checklist body. The content is type-generic for `comp_req` and `feat`; see fixtures for exact content.

For types not covered by built-in templates (anything beyond `feat`, `comp_req`, `story`, `use_case`, `spec`, `impl`, `test`), emit a minimal checklist with `- [ ] Review this <type> for clarity, correctness, and traceability.`

Additionally, emit `checklists/requirement.md` as a canonical alias for the primary requirement-type checklist (the `comp_req` checklist if declared, otherwise whichever declared type has prefix `REQ_` / role `requirement` per artefact-catalog.yaml). The alias is a one-line redirect `# See [<directive>.md](<directive>.md) — canonical requirement checklist` plus the frontmatter block. Downstream skills (`pharaoh-tailor-review`, `pharaoh-req-review`) reference `checklists/requirement.md` as the well-known filename, so the alias keeps the interop contract stable regardless of the project's directive naming.

### Step 6: Check overwrite + write

For each target file, check existence. If exists and `overwrite=false`, add to `files_skipped`, emit warning `"<path> already exists; skipping (use overwrite=true to regenerate)"`. Otherwise write the file and add to `files_created`.

Create intermediate directories (`.pharaoh/project/`, `.pharaoh/project/checklists/`) as needed.

### Step 7: Return

Return the JSON report.

## Failure modes

- `ubproject.toml` missing → FAIL.
- Zero types declared → FAIL per Step 1.
- `.pharaoh/project/` unwritable → FAIL.

## Non-goals

- No tailoring inference from corpus statistics. For that, use `pharaoh-tailor-detect` + `pharaoh-tailor-fill` on matured projects.
- No pharaoh.toml generation. That is `pharaoh-setup`.
- No sphinx-needs config generation. That is `pharaoh-bootstrap`.
- No checklist customization per project — checklists are built-in templates. Caller edits after generation.

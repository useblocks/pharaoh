---
name: pharaoh-req-code-grounding-check
description: Use when verifying a single drafted requirement against the source file it cites via `:source_doc:`. Single mechanical fidelity check — compares the CREQ's claims about exceptions, triggers, types, structural symbols, backtick-quoted identifiers, grounding density, adjectives, quantifiers, and branch count against the cited source, returning per-axis findings JSON. Complements `pharaoh-req-review` (which grades prose quality) with code-grounded axes.
---

# pharaoh-req-code-grounding-check

## When to use

Invoke as a sibling review alongside `pharaoh-req-review` whenever an emission skill (e.g. `pharaoh-req-from-code`) has just produced a requirement that declares `:source_doc:`. Reads the RST directive block + the cited source file, emits findings JSON with per-axis pass/fail so the caller can decide whether to finalize, regenerate, or reject the requirement.

Do NOT use to grade prose quality (atomicity, verifiability, ambiguity) — that is `pharaoh-req-review`. Do NOT use for requirements lacking `:source_doc:` — axis #8 will fail immediately and the remaining axes cannot be evaluated. Do NOT use to re-author or modify the requirement — this skill is read-only and emits findings only.

## Atomicity

- (a) Indivisible: one CREQ + one source file in → one findings JSON out. No re-authoring, no set-level analysis, no dispatch of other skills.
- (b) Input: `{target: <need_id_or_rst>, source_doc_path: <str>, tailoring_path: <str>}`. Output: findings JSON per the shape in `## Output` below.
- (c) Reward: fixtures under `skills/pharaoh-req-code-grounding-check/fixtures/` — one per failure mode:
  1. `passing-case/` — all axes pass; matches `expected-output.json` (`overall: "pass"`, empty `blockers`).
  2. `dead-exception/` — CREQ names 5-class hierarchy; source raises 2 of 5 → `exception_raise_sites_exist` fails with 3 missing names in `evidence`.
  3. `inverted-trigger/` — CREQ says `when origin == "Sphinx-Needs"`; source has `if origin != "Sphinx-Needs"` → `trigger_condition_literal_match` fails.
  4. `pydantic-halluc/` — CREQ says "Pydantic model"; source imports `dataclasses` → `type_framework_matches_imports` fails.
  5. `weasel-adjectives/` — CREQ body contains `structured`, `comprehensive`, `full` → `no_weasel_adjectives` fails with the 3 matches in `evidence`.
  6. `unbounded-all/` — CREQ says "all validation errors" without enumeration → `quantifier_enumerated` fails.
  7. `collapsed-branches/` — CREQ is one shall-clause; source function has 4 visible branches → `branch_count_aligned` scores 1.
  8. `misattributed-config-field/` — CREQ body backtick-cites a default literal and a config field name; declared source_doc is the consumer module which uses them only through attribute access. Fixture ships a `code-grounding-filters.yaml` enabling the `cross_file_literal_default` strategy so the skill can emit the actionable "lives in config, cite attribute instead" evidence. Without the YAML the tokens would still fail axis #5 with the generic "not in source_doc" message.
  9. `typer-kebab-filter/` — CREQ body cites ``--license-key``; source defines `license_key` as a Typer parameter. Fixture ships a `code-grounding-filters.yaml` enabling `kebab_to_snake_or_pascal` with `morphology_prefixes: ["Opt"]`. The filter resolves; without the YAML, universal filters do not cover this pattern and the axis would fail.
  10. `toml-section-filter/` — CREQ body cites ``[myapp.export_config]``; skipped by universal filter #1 (TOML section). No tailoring YAML required.
  11. `external-dotted-path/` — CREQ body cites ``rich.console.Console``; source imports `from rich.console import Console`. Fixture ships a `code-grounding-filters.yaml` enabling `dotted_import_resolution` with the Python separator / import patterns. Without the YAML, universal filters do not cover this pattern.
  12. `env-var-glob/` — CREQ body cites ``JAMA_*``; source defines `JAMA_URL_ENV`, `JAMA_USERNAME_ENV`, etc. Fixture ships a `code-grounding-filters.yaml` enabling `prefix_glob_expansion`. Without the YAML, universal filters do not cover this pattern.
  13. `abstract-prose/` — CREQ body uses only "the component shall" / "caller-configured" with zero backtick-quoted identifiers; fails axis #8 (`source_doc_resolves`) because the file contains no symbols the shall clause names, exposing that the CREQ is untestable against the cited file. No tailoring YAML required — axis mechanics are language-agnostic.

  Pass = all 13 fixture outputs match `expected-output.json` modulo `evidence` field substring match.
- (d) Reusable across projects — any corpus whose CREQs declare `:source_doc:`. Two extension points, both optional: (i) weasel blacklist via `tailoring.weasel_extra`; (ii) axis-#5 pluggable language-specific filter chain via `code-grounding-filters.yaml` (schema: [`shared/code-grounding-filters.md`](../shared/code-grounding-filters.md)). Without any tailoring the skill runs three universal axis-#5 filters and the base weasel blacklist — stricter signal, language-agnostic, usable in any project out of the box.
- (e) Read-only. Does not modify the CREQ RST or the source file. Never invokes other skills (caller runs `pharaoh-req-review` as a sibling).

## Input

- `target`: either a `need_id` resolvable in `needs.json`, or a raw RST directive block for one CREQ. The block must contain the `:source_doc:` option; if absent, axis #8 (`source_doc_resolves`) fails with `"source_doc missing — cannot ground check"` and every other axis records `passed: "n/a"`.
- `source_doc_path` (optional when `target` is an RST block): path to the cited source file. Accepts either an absolute path or a path relative to `project_root`; relative paths are joined with `project_root` before opening. Extension determines the raise-site / import regex flavour (Python MVP; other languages via `shared/public-symbol-patterns.md`). If the resolved path does not exist, axis #8 fails with `"source_doc unresolved"`. When `target` is a raw RST block AND `source_doc_path` is omitted, the skill auto-derives it from the block's `:source_doc:` option and resolves via `project_root`.
- `project_root` (optional, required when `source_doc_path` is relative or omitted): absolute path to the consumer project's root. Used to resolve relative or auto-derived source docs to absolute paths before opening.
- `tailoring_path`: absolute path to the project's tailoring directory (`.pharaoh/project/`). Two files are read:
  - `checklists/requirement.md` frontmatter for `tailoring.weasel_extra: [<word>, ...]` (axis #6 extension).
  - `code-grounding-filters.yaml` for axis #5's pluggable language-specific filter chain; schema in [`shared/code-grounding-filters.md`](../shared/code-grounding-filters.md). Missing, empty, or malformed YAML is acceptable — only the three universal filters apply.

Edge cases: empty source file → axes #1, #2, #3, #4, #5, #9 fail with `"source file empty"` evidence (axes that read the source body); missing tailoring file → base blacklist applies silently, no pluggable filters load; malformed `code-grounding-filters.yaml` → skill logs a warning in `notes`, falls back to universal filters only; language-specific axes (#1 raise-sites, #2 trigger, #3 named-symbol) use the Python MVP regex by default and record `passed: "n/a", reason: "language not yet supported"` for non-Python sources where the regex does not apply.

## Output

```json
{
  "need_id": "REQ_example_read",
  "source_doc": "src/example/reader.py",
  "axes": {
    "exception_raise_sites_exist":    {"passed": false, "evidence": "ReadError cited; 1 raise site found in reader.py:159 — PASS; UnicodeDecodeError cited as raised, 0 raise sites — FAIL"},
    "trigger_condition_literal_match": {"passed": true},
    "named_symbol_exists":             {"passed": true},
    "type_framework_matches_imports":  {"passed": "n/a", "reason": "no type-framework claim in body"},
    "backtick_symbol_in_source_doc":   {"passed": false, "evidence": "4 backtick tokens checked: 'read_file' ✓, 'strict' ✓, 'uuid_target' ✓, 'reqif_uuid' ✗ (not in reader.py, lives in config/reqif_config.py — cross-file leak)"},
    "no_weasel_adjectives":            {"passed": false, "evidence": "'structured diagnostic' — 'structured' blacklisted"},
    "quantifier_enumerated":           {"passed": false, "evidence": "'all unrecoverable input failures' — unbounded 'all' without enumeration"},
    "source_doc_resolves":             {"passed": true},
    "branch_count_aligned":            {"score": 1, "evidence": "function read_file has 4 visible branches (encoding err / parse err / empty / success); CREQ is one shall-clause"}
  },
  "overall": "fail",
  "blockers": ["exception_raise_sites_exist", "backtick_symbol_in_source_doc", "no_weasel_adjectives", "quantifier_enumerated"],
  "actions": [
    "Remove 'UnicodeDecodeError raised' claim OR add raise site for UnicodeDecodeError in reader.py",
    "Replace 'reqif_uuid' with the consumer-side attribute form (e.g. 'uuid_target' accessed via 'self.config.uuid_target') OR change :source_doc: to config/reqif_config.py",
    "Replace 'structured diagnostic' with concrete term (list[str])",
    "Enumerate 'all unrecoverable input failures' or replace with specific classes"
  ]
}
```

`overall` is `"pass"` iff every mechanical axis has `passed: true` (or `"n/a"`) AND `branch_count_aligned.score >= 2`. Any mechanical `passed: false` OR a branch-count score of 0 or 1 promotes the axis name into `blockers` and sets `overall: "fail"`. `actions` enumerates one remediation per blocker, with enough specificity to guide regeneration.

## Detection rule

Eight mechanical axes plus one subjective axis. Every mechanical axis resolves to a grep over the CREQ body and/or the source file; no LLM judgement on mechanical axes. Axes are listed in the order they should execute — cheap greps first, so a failing body short-circuits before expensive AST / import resolution on axes 4, 7, and 9.

### 1. `exception_raise_sites_exist`

**Check:** For each class name `X` mentioned in a `raises X` / `shall raise X` / `throws X` clause in the CREQ body, grep `raise X(` in the source file. Each cited class must have ≥1 raise site. Missing raise sites promote the axis to `passed: false` with the evidence listing every missing class name.

**Detection:**
```bash
# Extract cited exceptions from CREQ body:
grep -oE '(?:raises?|throws?|shall raise)\s+(?:the\s+|an?\s+)?[A-Z][A-Za-z0-9_]+' <creq> \
  | awk '{print $NF}' | sort -u
# For each, verify raise site in source:
grep -cE "raise\s+<X>\s*\(" <source_doc>
```

### 2. `trigger_condition_literal_match`

**Check:** Detect `when <field> == "<value>"` / `when <field> is <value>` in the CREQ body. Extract `<field>` and `<value>`. Grep source for `<field>\s*==\s*"<value>"` vs `<field>\s*!=\s*"<value>"`. Mismatch between claimed operator / value and the source code fails.

**Detection:**
```bash
grep -oE 'when\s+[a-z_]+\s*(==|is)\s*"[^"]*"' <creq>
# then in source:
grep -E '<field>\s*(==|!=)\s*"<value>"' <source_doc>
```

### 3. `named_symbol_exists`

**Check:** Extract symbol names from the CREQ body ONLY in bounded structural contexts:

- Verb-prefix pattern: `(?:raises?|throws?|uses?|wraps?|calls?|invokes?|extends?|subclasses?)\s+(?:the\s+|an?\s+)?(?P<sym>[A-Z][A-Za-z0-9_]+)`
- Function-call shape: `(?P<fn>[a-z_][a-z0-9_]+)\(`

Every extracted `sym` / `fn` must appear as a definition or call site in the source file. This narrowing — verb prefix OR trailing parens — is load-bearing: unrestricted `[A-Z][a-zA-Z0-9]+` matching produces false positives on stdlib generics (`List`, `Dict`, `Optional`) and sentence-initial capitalization (`Parser`, `User`).

**Detection:**
```bash
grep -E "(raises?|throws?|uses?|wraps?|calls?|invokes?|extends?|subclasses?)\s+(the\s+|an?\s+)?[A-Z][A-Za-z0-9_]+" <creq>
grep -E "[a-z_][a-z0-9_]+\(" <creq>
# each extracted name must exist in <source_doc> as def/class/call site
```

### 4. `type_framework_matches_imports`

**Check:** If CREQ body mentions "Pydantic model", source must `from pydantic import ...` or `import pydantic`. "dataclass" → source must have `@dataclass` or `from dataclasses`. "attrs class" → `@attr` or `import attr`. "TypedDict" → `from typing import TypedDict` or `typing.TypedDict`. Mismatch between the claim and the imports fails.

**Detection:**
```bash
grep -oEi 'pydantic|dataclass|attrs\s+class|typeddict' <creq>
# Python imports:
grep -E '^(from|import)\s+(pydantic|dataclasses|attr|typing)' <source_doc>
grep -E '^@(dataclass|attr\.s|attrs\.define)' <source_doc>
```

### 5. `backtick_symbol_in_source_doc`

**Check:** For every backtick-quoted token ``` ``X`` ``` in the CREQ body, verify that `X` appears as a literal substring in the declared `:source_doc:`. This catches cross-file leaks that the verb-prefixed axis #3 (`named_symbol_exists`) misses, because many backtick-cited identifiers sit in running prose without a structural verb in front of them (e.g. "honouring ``include_links`` and per-field delimiters").

The check runs **after** normalising the token through a two-tier filter chain: three universal filters built into the base skill plus zero or more pluggable language-specific filters loaded from `<tailoring_path>/code-grounding-filters.yaml`. Tokens surviving both tiers are looked up in the source file; the first unresolved token fails the axis with `evidence` naming each unresolved token and — when the token is found elsewhere in the project source tree — the file it actually lives in, so the caller knows whether to retarget `:source_doc:` or rewrite the CREQ.

#### Universal filters (always active, language-agnostic)

Apply in order; a token that matches any step is counted as resolved (or skipped) without penalty.

1. **TOML section / table header** — token matches `^\[[a-z_][\w.]*\]$` (e.g. ``[myapp.export_config]``, ``[foo]``). Not a code identifier in any language; skip.
2. **File path / command-string** — token contains `/` or a space (e.g. ``commands/csv.py``, ``jama check``). Skip; file paths are covered by axis #8 (`source_doc_resolves`) and multi-word strings are user-facing UI text, not code symbols. Language-agnostic — `/` and whitespace are not valid identifier characters in any mainstream language.
3. **Short-prose guard** — tokens that are lowercase English words under 4 chars (e.g. ``id``, ``to``, ``or``) OR all-caps domain acronyms in a closed list (``API``, ``CSV``, ``JSON``, ``REST``, ``TOML``, ``CLI``, ``URL``, ``HTTP``) are treated as prose, not symbols. Skip. The acronym list is conservative and stays in the base skill.

#### Pluggable filters (from tailoring YAML)

After the three universal filters run, the skill loads `<tailoring_path>/code-grounding-filters.yaml` (if present) and applies every filter declared there in order. The YAML schema and the four supported strategies (`kebab_to_snake_or_pascal`, `prefix_glob_expansion`, `dotted_import_resolution`, `cross_file_literal_default`) are documented in [`shared/code-grounding-filters.md`](../shared/code-grounding-filters.md). Each strategy is a parameterised shape; projects supply the language-specific regex / separator / patterns per strategy. Python / Typer projects get CLI-kebab + env-glob + stdlib-import + dataclass-default filters; Rust / Clap projects get the same strategies with different patterns (`use X::Y`, `#[serde(default=...)]`). An absent YAML means only the universal filters run — acceptable default, stricter signal, no wrong-language false negatives.

Any token that fails every filter AND does not literally appear in `:source_doc:` fails the axis.

**Detection (pseudocode):**
```python
for tok in re.findall(r'``([^`]+)``', creq_body):
    # Tier 1 — universal filters (always active)
    if match_toml_section(tok): continue
    if '/' in tok or ' ' in tok: continue
    if is_short_prose(tok): continue

    # Tier 2 — pluggable filters from tailoring
    if any(f.resolves(tok, source_text, project_root)
           for f in tailored_filters):
        continue

    # Baseline — literal substring match
    if tok in source_text: continue

    # Not resolved — record with cross-file lookup for evidence
    elsewhere = locate_in_project(tok, project_root)
    violations.append({"token": tok, "found_in": elsewhere})
```

The ordering is load-bearing: universal filters short-circuit before the YAML is even opened, so missing-tailoring projects pay zero cost for the three cheap greps. Pluggable filters run before the baseline substring check so that language-specific resolutions take precedence over accidental substring coincidences.

### 6. `no_weasel_adjectives`

**Check:** Grep the CREQ body against the base blacklist:

```
structured, comprehensive, full, absolute, paginated, robust, complete, proper
```

Any match fails with the matched word in evidence. These words imply mechanised behaviour without grounding. Tailoring extension: `tailoring.weasel_extra` (list) is union-merged with the base before the grep.

**Detection:**
```bash
grep -iwE '\b(structured|comprehensive|full|absolute|paginated|robust|complete|proper)\b' <creq>
```

### 7. `quantifier_enumerated`

**Check:** Narrow, mechanical quantifier detection only. Regex:

```
\b(?:all|every|each)\s+(?:[a-z]+\s+){0,3}(?:error|errors|exception|exceptions|failure|failures|case|cases|command|commands|branch|branches|mode|modes|validator|validators)s?\b
```

If matched, the same sentence or the next sentence must contain either:
- `:\s` (enumeration colon), OR
- ` namely ` / ` specifically ` / ` including ` (enumeration marker), OR
- a Sphinx list directive (`.. list-table::` / `- ` bullet in an adjacent block).

Otherwise fail. Broader quantifier judgement — "does 'the system' implicitly quantify?" — is deferred to the subjective `unambiguity_prose` axis in `pharaoh-req-review`. This axis catches only the specific pattern where the noun signals an expected enumeration that is missing.

### 8. `source_doc_resolves`

**Check:** The CREQ's `:source_doc:` option must (a) be present, (b) point at an existing file, and (c) the file must contain at least one symbol the CREQ names (per axis #3 extraction). Three fail modes:

- `:source_doc:` absent → `passed: false, evidence: "source_doc missing — cannot ground check"`.
- Path does not exist → `passed: false, evidence: "source_doc unresolved: <path>"`.
- Symbols from CREQ body absent in file → `passed: false, evidence: "source_doc-symbol mismatch: none of [<sym>, ...] found in <path>"`.

### 9. `branch_count_aligned` (subjective, 0-3)

**Check:** Count `if` / `elif` / `else` / `match` branches in the function named by `:source_doc:` (parse via Python `ast` where available, regex fallback). If CREQ is one shall-clause but the function has ≥3 branches producing visibly different outputs, score ≤ 2. If CREQ enumerates branches or is a set of short CREQs covering them, score 3.

Rubric:
- 3 — CREQ structure matches source branch count (1 shall per branch, or a single CREQ with explicit per-branch enumeration).
- 2 — CREQ groups branches under a justified umbrella (e.g. "validation errors" for 2-3 similar branches).
- 1 — CREQ collapses ≥3 distinct branches into one shall-clause with no enumeration; different projects would reasonably want these split.
- 0 — CREQ omits entire branches that produce observable output.

## Tailoring extension point

See [`shared/checklists/requirement.md`](../shared/checklists/requirement.md) — the canonical location of the `tailoring.weasel_extra` frontmatter key consumed by axis #6 (`no_weasel_adjectives`). No other project-specific state in the base skill; all regulatory-standard vocabulary (ASIL, ARC, ASPICE process IDs) stays out of the base.

## Composition

Role: `atom-check`.

Called as a sibling alongside `pharaoh-req-review` from the `## Last step` of any emission skill that drafts requirements with `:source_doc:` (e.g. `pharaoh-req-from-code`). The two atoms run independently; neither dispatches the other. The caller merges findings under `review.iso_axes` (from req-review) and `review.code_grounding` (from this skill). Emission fails if either atom returns a mechanical-axis failure.

Never invoked directly by end users — always from an emission skill's Last step or from `pharaoh-quality-gate.required_checks` in invariant-delegation mode.

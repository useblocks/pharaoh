---
name: requirement
applies_to: comp_req
axes:
  - atomicity
  - internal_consistency
  - verifiability
  - schema
  - source_doc_resolves
  - unambiguity_prose
  - comprehensibility
  - feasibility
  - completeness
  - external_consistency
  - no_duplication
  - maintainability
  - exception_raise_sites_exist
  - trigger_condition_literal_match
  - named_symbol_exists
  - type_framework_matches_imports
  - backtick_symbol_in_source_doc
  - no_weasel_adjectives
  - quantifier_enumerated
  - branch_count_aligned
---

# Requirement review checklist

Generic baseline for reviewing a single requirement-level need against ISO 26262-8 §6 axes plus
code-grounding fidelity axes. Domain-neutral — no regulatory-standard-specific vocabulary, no
downstream-consumer link names. Projects add tailoring addenda under
`.pharaoh/project/checklists/requirement.md`.

## Mechanized axes (pass/fail, execution-based reward)

### atomicity

**Check:** The body contains exactly one `shall` clause and no coordinating conjunction joins modal
verbs within that clause.

**Detection rule:**
```bash
grep -cE '\bshall\b' <creq_body>                      # must equal 1
grep -E 'shall .*(, and | and | or |, or )' <creq_body>   # must return no match
```

### internal_consistency

**Check:** The body contains no self-contradictory phrasing (simultaneous "always" and "unless not
required", or an exception that negates the main clause).

**Detection rule:**
```bash
grep -E '\b(always|must)\b.*\bunless\b|\balways\b.*\bnever\b' <creq_body>
```

### verifiability

**Check:** The directive has a `:verification:` (or project-declared equivalent) option, non-empty,
whose target resolves in `needs.json`.

**Detection rule:** extract `:verification:` option; look up the value in the needs map; pass iff
the key exists.

### schema

**Check:** Every field listed under `required_fields` for this artefact type in
`artefact-catalog.yaml` is present and non-empty in the directive options.

**Detection rule:** parse directive options; diff keys against the catalog's required list; pass
iff the diff is empty.

### source_doc_resolves

**Check:** If the artefact catalog declares `:source_doc:` for this type, the option must be
present, point at an existing file, and the file must contain at least one symbol named in the
requirement body. Runs whenever `:source_doc:` is declared, independent of any grounding-check
invocation. See `../../pharaoh-req-code-grounding-check/SKILL.md#axes` for symbol-extraction
details.

**Detection rule:**
```bash
grep -oE ':source_doc:\s+\S+' <creq>                   # option present
test -f "<source_doc_value>"                           # path resolves
grep -qE '<extracted_symbol>' "<source_doc_value>"     # ≥1 symbol hit
```

## Subjective axes (0-3, LLM-judge fallback)

### unambiguity_prose

- 3 — Single interpretation; measurable terms; no weasel adjectives.
- 2 — Single interpretation; minor phrasing issues.
- 1 — Two plausible interpretations; a vague term like "sufficient" without a threshold.
- 0 — Multiple conflicting interpretations.

### comprehensibility

- 3 — Reader at adjacent abstraction level understands without supporting documents.
- 2 — Mostly clear; minor jargon or an undefined acronym.
- 1 — Mostly unclear without extra context.
- 0 — Reader at adjacent level cannot follow.

### feasibility

- 3 — Clearly feasible, tightly bounded.
- 2 — Feasible with known engineering effort.
- 1 — Feasible but significant unknowns.
- 0 — Obviously infeasible within item-development constraints.

## Deferred / chain-level axes

`completeness`, `external_consistency`, `no_duplication` require the full set of sibling
requirements — assessed by a set-level review atom, not here. Record as
`{"score": "deferred", "reason": "set-level axis"}`. `maintainability` requires observing
regeneration convergence — record as `{"score": null, "reason": "chain-level axis"}`.

## Mechanised axes — code-grounded

Runs only when the requirement declares `:source_doc:`. Paired with the runner at
`../../pharaoh-req-code-grounding-check/SKILL.md` — this checklist is the rubric reference, the
skill is the runner. See `../../pharaoh-req-code-grounding-check/SKILL.md#axes` for full axis
prose; entries below are the grep-able detection rules the runner applies.

### exception_raise_sites_exist

**Check:** Every exception class named in a `raises X` / `shall raise X` / `throws X` clause in the
body has at least one raise site in `:source_doc:`.

**Detection rule:**
```bash
grep -oE '(raises?|throws?|shall raise)\s+(the\s+|an?\s+)?[A-Z][A-Za-z0-9_]+' <creq_body> \
  | awk '{print $NF}' | sort -u
# for each extracted class X, verify:
grep -cE "raise\s+X\s*\(" <source_doc>   # must be ≥ 1
```

### trigger_condition_literal_match

**Check:** For each `when <field> == "<value>"` / `when <field> is <value>` clause in the body, the
source file contains the matching operator and literal — not an inverted `!=` / different value.

**Detection rule:**
```bash
grep -oE 'when\s+[a-z_]+\s*(==|is)\s*"[^"]*"' <creq_body>
# then verify the same operator / literal in <source_doc>:
grep -E '<field>\s*(==|!=)\s*"<value>"' <source_doc>
```

### named_symbol_exists

**Check:** Every symbol mentioned in a structural context (after `raises/throws/uses/wraps/calls/
invokes/extends/subclasses`, or as a function-call with parens) exists as a definition or call
site in `:source_doc:`. Bounded extraction avoids false positives on stdlib generics and narrative
capitalization.

**Detection rule:**
```bash
grep -E '(raises?|throws?|uses?|wraps?|calls?|invokes?|extends?|subclasses?)\s+(the\s+|an?\s+)?[A-Z][A-Za-z0-9_]+' <creq_body>
grep -E '[a-z_][a-z0-9_]+\(' <creq_body>
# each extracted name must appear in <source_doc>:
grep -E '(def|class)\s+<name>|<name>\s*\(' <source_doc>
```

### type_framework_matches_imports

**Check:** If the body cites a type-framework (`Pydantic model`, `dataclass`, `attrs class`,
`TypedDict`), the source file's imports match. Naming a `FooError`-shaped Pydantic model while the
source uses `@dataclass` fails.

**Detection rule:**
```bash
grep -oEi 'pydantic|dataclass|attrs\s+class|typeddict' <creq_body>
grep -E '^(from|import)\s+(pydantic|dataclasses|attr|typing)' <source_doc>
grep -E '^@(dataclass|attr\.s|attrs\.define)' <source_doc>
```

### backtick_symbol_in_source_doc

**Check:** Every backtick-quoted token in the body — surviving the filter chain (TOML section,
file path / CLI string, Typer kebab flag, env glob, external dotted path, short-prose acronym) —
must appear as a literal substring in the file named by `:source_doc:`. Catches the cross-file
leak where a CREQ cites a config-side default literal (e.g. ``reqif_uuid``) while its
`:source_doc:` points at the consumer module that only sees the attribute (`self.config.uuid_target`).

**Detection rule:** delegated to `pharaoh-req-code-grounding-check` axis #5 — see that skill for the
full filter chain and evidence format. The check runs per-CREQ during the sibling-review phase.

### no_weasel_adjectives

**Check:** The body contains no word from the base blacklist
`structured, comprehensive, full, absolute, paginated, robust, complete, proper` nor any entry
added via `tailoring.weasel_extra`. These words imply mechanised behaviour without grounding.

**Detection rule:**
```bash
grep -iwE '\b(structured|comprehensive|full|absolute|paginated|robust|complete|proper)\b' <creq_body>
# extended blacklist resolved at runtime from tailoring.weasel_extra
```

### quantifier_enumerated

**Check:** If the body contains an unbounded quantifier over an enumerable noun
(`all errors`, `every validator`, `each branch`, ...), the same or next sentence must enumerate
the members (colon + list, `namely`, `specifically`, `including`, or a Sphinx list directive).

**Detection rule:**
```bash
grep -oE '\b(all|every|each)\s+([a-z]+\s+){0,3}(error|errors|exception|exceptions|failure|failures|case|cases|command|commands|branch|branches|mode|modes|validator|validators)s?\b' <creq_body>
# then require in the same or next sentence:
grep -E ':\s|\s(namely|specifically|including)\s|\.\.\s+list-table::|^\s*-\s' <adjacent_block>
```

### branch_count_aligned (subjective, 0-3)

**Check:** Count `if` / `elif` / `else` / `match` branches in the function named by `:source_doc:`.
Score by how well the requirement structure reflects the branch count.

**Rubric:**
- 3 — One shall per branch, or a single requirement with explicit per-branch enumeration.
- 2 — Branches grouped under a justified umbrella (e.g. "validation errors" for 2-3 similar branches).
- 1 — Requirement collapses ≥3 distinct branches into one shall-clause with no enumeration.
- 0 — Requirement omits entire branches that produce observable output.

**Detection rule:**
```bash
python3 -c "import ast,sys; t=ast.parse(open(sys.argv[1]).read()); \
  print(sum(isinstance(n,(ast.If,ast.Match)) for n in ast.walk(t)))" <source_doc>
# regex fallback for non-Python:
grep -cE '^\s*(if|elif|else|match)\b' <source_doc>
```

## Tailoring extension point

Per-project addenda under `.pharaoh/project/checklists/requirement.md` add axes with keys prefixed
`tailoring.*`. Frontmatter-level tailoring knobs extend the base axes in place:

```yaml
tailoring:
  weasel_extra: ["comprehensively", "seamlessly", "flexibly"]
```

`weasel_extra` is union-merged with the base blacklist before `no_weasel_adjectives` runs.
Projects may also add their own axes:

- `tailoring.link_to_safety_goal` — for safety-critical domains that require a dedicated upstream
  link option beyond the base `:satisfies:`.
- `tailoring.controlled_vocabulary_used` — for corpora that mandate a glossary-backed term set.

Extension axes follow the same mechanized vs subjective split. The base axes are always run;
tailoring axes run only if the project defines them.

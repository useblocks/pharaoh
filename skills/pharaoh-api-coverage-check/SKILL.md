---
name: pharaoh-api-coverage-check
description: Use when verifying that a source file is covered by the need catalogue on two axes — (1) at least one CREQ declares the file as its `:source_doc:`, and (2) every project-defined exception class raised in the file is named by some CREQ's title or content. Exception classes not defined in the project source tree (stdlib, third-party deps) are reported as `external` and do not fail the axis. Classifies non-behavioral files (constants, type aliases, bare re-exports) as skipped. Language-parametric via the shared regex table in `skills/shared/public-symbol-patterns.md` (python / rust / typescript / go / c / cpp / java). Single mechanical structural check.
---

# pharaoh-api-coverage-check

## When to use

Invoke from `pharaoh-quality-gate.required_checks` (invariant `api_coverage_clean`), from a pre-release CI job, or standalone when auditing whether the need catalogue has kept pace with the code. Reads one source file plus one `needs.json` and emits a binary verdict on two axes — file-level citation AND raise-site coverage. Non-behavioral files (constants, type aliases, bare re-exports) are skipped so they never fail the gate.

This is the reverse coverage direction of `pharaoh-req-from-code`. The forward direction answers "for this file, which reqs should be drafted?". The reverse direction answers "does the catalogue acknowledge this file's existence AND every exception it raises?". Missing coverage here points at CREQs that were never authored, not at CREQs that are poorly written.

Do NOT use to grade need prose quality — that is `pharaoh-req-review`. Do NOT use to verify that a CREQ's claims about the file are accurate — that is `pharaoh-req-code-grounding-check` (the forward fidelity check). Do NOT use to author or modify reqs (read-only). Python classification runs on an AST; other languages use regex approximations consistent with the shared public-symbol-patterns table.

## Atomicity

- (a) Indivisible: one source file + one `needs.json` in → one findings JSON out. No req drafting, no set-level analysis, no dispatch of other skills.
- (b) Input: `{source_file: str, needs_json_path: str, project_root: str | null, language: "auto" | "python" | "rust" | "typescript" | "go" | "c" | "cpp" | "java"}`. Output: findings JSON per the shape in `## Output` below.
- (c) Reward: fixtures under `skills/pharaoh-api-coverage-check/fixtures/` cover each verdict class and each supported language. Pass = each fixture's actual output matches `expected-output.json` modulo ordering of the `covered`, `uncovered`, and `external` arrays under `raise_site_coverage` (sorted ascending in the emitted output) and of `file_coverage.citing_creqs` (sorted ascending).
- (d) Reusable across projects — the language regex table is read from `skills/shared/public-symbol-patterns.md`, not inlined. No project-specific symbol names baked in.
- (e) Read-only. Does not modify the source file, `needs.json`, or any on-disk state. Running twice on identical inputs yields byte-identical output.

## Input

- `source_file`: absolute path to the source file under audit, OR a path relative to `project_root`. Extension is used for language inference when `language=auto`.
- `needs_json_path`: absolute path to the built sphinx-needs corpus `needs.json`. Accepts either the flat `{"needs": {<id>: {...}}}` shape or the versioned `{"versions": {"<v>": {"needs": {...}}}}` shape. Each need dict must carry at least `id`, `title`, and `content` (or a synonymous body field); the `source_doc` option is what the file-coverage axis reads.
- `project_root`: optional absolute path. Used for three things: (1) resolve `source_file` when relative, (2) resolve a need's `:source_doc:` value when relative, (3) scope the project-definition scan that distinguishes project-defined exception classes from external (stdlib / third-party) ones in raise-site coverage. When omitted, relative paths are resolved against the current working directory and the project-definition scan is skipped — every raised class is then treated as project-defined.
- `language`: one of `"auto"`, `"python"`, `"rust"`, `"typescript"`, `"go"`, `"c"`, `"cpp"`, `"java"`. Default `"auto"`. When `"auto"`, the skill resolves the language from the source-file extension via the globs column of `skills/shared/public-symbol-patterns.md`. When an explicit language is given, extension is ignored — this is the dogfood escape hatch for literate source (e.g. a `.txt` with Python snippets).

Edge cases:
- `source_file` missing or unreadable → `overall: "fail"`, blocker `"source_file unresolved: <path>"`.
- `needs_json_path` missing or unparseable → `overall: "fail"`, blocker `"needs.json unresolved: <path>"`.
- `language="auto"` and extension matches no row in the shared table → `overall: "fail"`, blocker `"unsupported language: <ext>"`, `language: "unknown"`.

## Output

```json
{
  "source_file": "/abs/path/src/module/client.py",
  "language": "python",
  "classification": "behavioral",
  "file_coverage": {
    "passed": true,
    "citing_creqs": ["CREQ_inventory_client", "CREQ_inventory_load"]
  },
  "raise_site_coverage": {
    "total": 2,
    "project_defined": 1,
    "covered": ["InventoryError"],
    "uncovered": [],
    "external": ["ValueError"],
    "passed": true
  },
  "overall": "pass",
  "blockers": []
}
```

Fields (in canonical order):
- `source_file`: echo of the input path (as supplied — absolute or `project_root`-relative).
- `language`: resolved language string (one of the seven supported names) or `"unknown"` on unsupported-language failure.
- `classification`: `"behavioral"` or `"non-behavioral"`.
- `file_coverage.passed`: `true` iff ≥1 CREQ in the catalogue has `:source_doc:` resolving to this file. `null` when `classification == "non-behavioral"`.
- `file_coverage.citing_creqs`: list of CREQ IDs whose `:source_doc:` resolves to this file, sorted ascending. Empty list when no CREQ cites the file; still emitted for `non-behavioral` classification (diagnostic).
- `raise_site_coverage.total`: count of distinct exception class names extracted from `raise` / `throw` sites in the file.
- `raise_site_coverage.project_defined`: count of those names that resolve to a class / struct / enum defined somewhere under `project_root` for the file's language (see `## Project-definition scan`). `external` = `total - project_defined`.
- `raise_site_coverage.covered`: list of project-defined raised class names that appear (case-sensitive substring) in the title or content of some CREQ anywhere in the catalogue (not scoped to citing CREQs), sorted ascending.
- `raise_site_coverage.uncovered`: list of project-defined raised class names absent from every CREQ's title and content, sorted ascending.
- `raise_site_coverage.external`: list of raised class names that do not resolve to any project-local class definition — stdlib exceptions, third-party dep types. Diagnostic only; does not contribute to the pass/fail decision. Sorted ascending.
- `raise_site_coverage.passed`: `true` iff `uncovered` is empty. `null` when `classification == "non-behavioral"`.
- `overall`:
  - `"pass"` — `classification == "behavioral"` AND `file_coverage.passed` AND `raise_site_coverage.passed`.
  - `"fail"` — `classification == "behavioral"` AND either sub-axis is false.
  - `"skipped"` — `classification == "non-behavioral"`.
- `blockers`: list of blocker strings (input errors — unreadable source, unreadable needs.json, unsupported language). Always present; empty list on pass / skipped / clean fail.

On input errors the shape still carries every field. `classification` is `"non-behavioral"`, `file_coverage.citing_creqs` is `[]`, `raise_site_coverage` carries `total: 0, project_defined: 0, covered: [], uncovered: [], external: []` with `passed: null`, and `blockers` is populated with the error strings.

## Path resolution

- `source_file` resolution: absolute path used verbatim; relative path joined with `project_root` (or CWD if unset), then normalised via `os.path.normpath` (resolve `./` and `../`, collapse double slashes). Comparison is case-sensitive on POSIX. On Windows drive-letter paths the drive letter and path separators are normalised case-insensitively.
- `source_doc` resolution per need: the need's `source_doc` option value is resolved the same way (absolute verbatim, relative joined with `project_root`). A need cites the file iff its resolved `source_doc` equals the resolved `source_file`.

## Process

### Step 1: Resolve the language

If `language == "auto"`, read the globs column of `skills/shared/public-symbol-patterns.md` and find the first row whose glob list contains the source file's extension. If no row matches, emit an error output with `language: "unknown"`, `classification: "non-behavioral"`, `overall: "fail"`, `blockers: ["unsupported language: <ext>"]`, and stop. If an explicit language is given, use it verbatim and skip extension resolution.

### Step 2: Classify the file

A file is `behavioral` iff ANY of the following holds:

1. **Non-trivial function body**: ≥1 function / async function / method whose body contains more than 2 top-level statements. A body of `pass`, `...`, a single return, a single expression, or a single delegation call does not qualify. Docstrings are statements but do not count (strip them before measuring length).
2. **Exception surface**: ≥1 `raise X(...)` statement anywhere in the file. For languages whose exception syntax is `throw`, the equivalent `throw X(...)` / `throw new X(...)` counts.
3. **Method-rich class**: ≥1 class whose body contains ≥2 method definitions (public or private — the count is structural, not visibility-scoped).

Otherwise the file is `non-behavioral`: constants, type aliases, bare re-exports, empty `__init__.py` forwarders. Emit `classification: "non-behavioral"`, `overall: "skipped"`, both sub-axes with empty content and `passed: null`, and stop.

**Python**: parse with `ast`. Count `FunctionDef`/`AsyncFunctionDef` body length after stripping the module-level / function-level docstring (the first statement if it is a bare `Expr(Constant(str))`); check for `Raise` nodes anywhere; count `FunctionDef`/`AsyncFunctionDef` children inside each `ClassDef`.

**Other languages**: regex approximations colocated in the language table below.

### Step 3: File coverage

Load `needs.json`, flatten the needs map, and collect every CREQ whose `source_doc` option resolves (per `## Path resolution`) to the input `source_file`. `file_coverage.passed` is `true` iff the collected list is non-empty; `file_coverage.citing_creqs` is the sorted list of their IDs.

### Step 4: Raise-site coverage

Extract every exception class name `X` from every `raise X(...)` / `throw X(...)` / `throw new X(...)` site across the file (de-duplicate).

For each `X`, classify as **project-defined** or **external** per `## Project-definition scan` below. External classes go into the `external` diagnostic list and are excluded from pass/fail evaluation.

For each project-defined `X`, check whether `X` appears (case-sensitive substring) in the `title` OR `content` (or synonymous body field) of any CREQ anywhere in the catalogue — NOT scoped to citing CREQs. `raise_site_coverage.passed` is `true` iff every project-defined `X` is covered.

### Step 5: Emit the findings JSON

Populate every field per the `## Output` shape. Sort `file_coverage.citing_creqs`, `raise_site_coverage.covered`, `raise_site_coverage.uncovered`, and `raise_site_coverage.external` ascending. Set `overall` per the rules in the output-field description.

## Project-definition scan

When `project_root` is provided, the skill walks the tree and collects every class-like definition name matching the input file's language:

- Python: `class X` top-level or nested.
- Rust: `struct X`, `enum X`.
- TypeScript: `class X`, `class X extends Y`, `export class X`, `export default class X`, plus `interface X` / `type X = ...` shapes used as error types.
- Go: `type X struct`, `type X interface`.
- Java: `class X`, `interface X`, nested declarations.
- C: `struct X` (C has no exception classes in practice — typically empty set).
- C++: `class X`, `struct X`.

Only files whose extension matches the language's glob (per the table) are scanned. The regex uses the `public symbol regex` column from `skills/shared/public-symbol-patterns.md` (named capture `name`) filtered to class-like kinds.

A raised class `X` is **project-defined** iff its name appears in the collected set. Otherwise `X` is **external** — stdlib (`ValueError`, `RuntimeError`, `java.lang.IllegalArgumentException`, `std::runtime_error`) or third-party dep types.

When `project_root` is omitted, the scan is skipped and every raised class is treated as project-defined (the `external` list is empty). This keeps the skill usable in single-file contexts but the external-filter value is only available when `project_root` is supplied.

## Language table

| language   | extension globs                    | classifier notes                                                                                                                                                                                     | raise-site regex                                                            |
|------------|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| python     | `*.py`                             | Parse with `ast`. Body length computed after stripping the leading docstring. Class methods counted via `FunctionDef`/`AsyncFunctionDef` children of `ClassDef`.                                     | `raise\s+(?P<exc>[A-Z][A-Za-z0-9_]+)\s*\(`                                  |
| rust       | `*.rs`                             | Function-body statement count via brace-delimited body plus `;`-terminated statement splitting (trailing expressions count as one statement). Methods in an `impl` block count as class methods.     | n/a — Rust uses `Result<E>` returns                                         |
| typescript | `*.ts`, `*.tsx`                    | Function-body statement count via brace-delimited body plus `;`-terminated statement splitting. Class methods counted inside `class` / `export class` blocks.                                        | `throw\s+(?:new\s+)?(?P<exc>[A-Z][A-Za-z0-9_]+)\s*\(`                        |
| go         | `*.go`                             | Function-body statement count via brace-delimited body plus `;`-or-newline-terminated statement splitting. Interface methods and struct methods counted toward the method-rich-class rule (Go has no `class` keyword — `type T struct` plus ≥2 methods declared as `func (r *T)` qualifies). | n/a — Go uses `error` return values                                         |
| java       | `*.java`                           | Function-body statement count via brace-delimited body plus `;`-terminated statement splitting. Methods counted inside `class` / `interface` blocks.                                                 | `throw\s+(?:new\s+)?(?P<exc>[A-Z][A-Za-z0-9_]+)\s*\(`                        |
| c          | `*.c`, `*.h`                       | Function-body statement count via brace-delimited body plus `;`-terminated statement splitting. C has no classes — method-rich-class rule vacuously unsatisfied.                                     | n/a — C uses integer return codes                                           |
| cpp        | `*.cpp`, `*.hpp`, `*.cc`, `*.h`    | Function-body statement count as in C. Methods counted inside `class` / `struct` blocks.                                                                                                             | `throw\s+(?:new\s+)?(?P<exc>[A-Z][A-Za-z0-9_]+)\s*\(`                        |

The regex-based classifiers for non-Python languages share the accuracy ceiling of `shared/public-symbol-patterns.md` — known false positives in comments/strings, conservative over-reporting.

## Detection rule

One mechanical check, implemented as the five-step process above. No LLM judgement.

## Failure modes

- **Regex false positives inside comments and strings (non-Python).** A `// throw new FooError(...)` line in a block comment at column 0 is extracted as a raise site. Python avoids this because it uses the AST.
- **Case-sensitive substring matching for raise-site coverage.** Deliberate: sphinx-needs ids and class names are case-sensitive in practice, and a CREQ that describes `refreshTokenError` does not cover `RefreshTokenError`. Projects whose naming convention differs between code and prose must normalise at authoring time.
- **Raise-site extraction is shallow.** `raise Exc(...)` / `throw new Exc(...)` literals are detected. A function that raises by calling a helper that raises is not counted here — the question is "does this source file raise this class?", not "does execution of this file ever produce this class?".
- **`source_doc` must be declared.** Needs without the option cannot be collected by step 3, so a file with no citing needs is marked uncovered even if its behavior is described in free-floating prose elsewhere. That is the design — a CREQ that does not declare which file it describes cannot honestly claim to cover that file.
- **Raise-site coverage is catalogue-wide.** A CREQ for `bar.py` that names `InventoryError` in its body does cover the raise of `InventoryError` in `foo.py`. This is intentional: exception types are shared surface that multiple CREQs may reference. Projects that want scoped coverage should narrow via `source_doc` filters downstream.

## Tailoring extension point

None. The language regex table is shared (`skills/shared/public-symbol-patterns.md`) — a project that needs a new language supports it by adding a row there plus a corresponding entry in this skill's language table, which benefits both `pharaoh-req-from-code` and this skill.

## Composition

Role: `atom-check`.

Called from `pharaoh-quality-gate` under the invariant key `api_coverage_clean` (pass requirement: `overall ∈ {"pass", "skipped"}`). Also callable standalone from any CI job that already knows which source files and which `needs.json` to feed it. Never dispatches other skills. Never modifies the source file or the need catalogue.

Complements `pharaoh-req-code-grounding-check`: that skill runs the forward direction (does the CREQ's cited exception actually get raised in the file?), this skill runs the reverse direction (does every raised exception have a covering CREQ?). The two atoms share the language-regex table but no other code — they answer genuinely different questions and fail on different inputs.

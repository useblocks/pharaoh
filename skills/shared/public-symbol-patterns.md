# Public-symbol regex patterns per language

Shared regex table consumed by every Pharaoh skill that needs to enumerate top-level public symbols in a source file — currently `pharaoh-req-from-code` (file → reqs, via `split_strategy: "top_level_symbols"`) and `pharaoh-api-coverage-check` (file classification as behavioral vs non-behavioral, plus raise-site extraction). Any future upgrade (tree-sitter, libclang, per-language AST) replaces this one table and both consumers benefit automatically.

## Table

| language   | extension globs                      | public symbol regex (named capture `name`)                                                              | private-prefix rule        |
|------------|--------------------------------------|---------------------------------------------------------------------------------------------------------|----------------------------|
| python     | `*.py`                               | `^(?:async\s+)?(?:def|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*[(:]`                                 | leading `_`                |
| rust       | `*.rs`                               | `^pub\s+(?:fn|struct|enum|trait)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)`                                    | n/a (only `pub` items match)|
| typescript | `*.ts`, `*.tsx`                      | `^export\s+(?:async\s+)?(?:function|class|const|let|interface)\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)`     | n/a (only `export` items match)|
| go         | `*.go`                               | `^(?:func|type)\s+(?P<name>[A-Z][A-Za-z0-9_]*)`                                                         | lowercase first letter      |
| c          | `*.c`, `*.h`                         | `^[A-Za-z_][A-Za-z0-9_\s\*]*\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{?`                      | leading `_` or `static`     |
| cpp        | `*.cpp`, `*.hpp`, `*.cc`, `*.h`      | `^(?:class|struct)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)` plus the C free-function regex for free fns      | leading `_` or `private:` section |
| java       | `*.java`                             | `^\s*public\s+(?:static\s+)?(?:class|interface|[A-Za-z_][A-Za-z0-9_<>]*)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)` | anything not declared `public` |

## How consumer skills read the table

1. The consumer is given (or infers) a `language` value (either explicit input or resolved from `file_path` extension against the globs column).
2. The consumer compiles the row's regex (Python `re.MULTILINE`, or an equivalent multi-line flag in whatever runtime). The pattern exposes one named capture group, `name`, which carries the public-symbol identifier.
3. The consumer runs the pattern over the source file's text and collects every `name` match.
4. The private-prefix rule is applied AFTER the match: matches whose `name` begins with the declared prefix (or otherwise satisfies the rule, e.g. lowercase-first-letter for Go, non-`public` for Java) are dropped from the public-symbol set. Rust and TypeScript rows do not need a post-filter because the regex itself already anchors on `pub` / `export`.
5. The consumer treats the resulting set as the canonical list of public symbols for that file.

Language inference from `file_path` uses the globs column: the first row whose glob list contains the file's extension wins. If no row matches, the consumer fails with `unsupported language` — it does not silently fall back to a default.

## MVP accuracy tradeoff

These are line-anchored regexes, not language-aware parsers. Known false-positive pattern: any of the regex keywords appearing inside a comment or string literal at column 0 will be matched as if it were a real definition.

```python
# "class Foo" mentioned in a docstring at the start of a line matches the python row
```

```rust
// pub fn example_in_doc_comment() — matches the rust row if the leading // is stripped by the host
```

For the coverage-gate use case this is acceptable: false-positive uncovered symbols show up as a small handful of ghost names that the author can manually dismiss, but false-negative uncovered symbols (a real public symbol that the regex misses) would silently hide API surface from the check. The regexes here are conservative in the direction that matters — they over-report candidates, so they never miss a genuine public definition.

When AST-precision parsing lands (tree-sitter is the likely path), it replaces this file and both consumers inherit the upgrade. The consumer contract (named capture `name`, glob-based language resolution, post-filter for private rule) is designed to remain stable across that swap.

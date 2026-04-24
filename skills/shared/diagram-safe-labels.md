# Diagram safe-label rule

Shared guidance for every Pharaoh skill that emits Mermaid or PlantUML diagram blocks (`pharaoh-feat-component-extract`, `pharaoh-feat-flow-extract`, and every `pharaoh-*-diagram-draft`).

## Why this exists

A dogfooding iteration shipped Mermaid sequence diagrams that passed `sphinx-build -nW --keep-going -b html` with zero warnings but rendered as `Syntax error in text` in the browser. sphinx-build treats the diagram body as an opaque literal and hands it to the Mermaid runtime at render time; any parse failure surfaces only when a human opens the page.

Classic silent failure. The root cause on one diagram was a semicolon inside a sequence message label:

```mermaid
sequenceDiagram
    J->>J: filter by type; skip SET/Folder
```

Mermaid 11's sequence grammar treats `;` as a statement terminator. Parser sees `filter by type` as the message, then hits `skip SET/Folder` and fails with `Expecting SOLID_ARROW ... got NEWLINE`.

## The rule

Inside any emitted label (message labels, edge labels, node labels, participant aliases, notes), the following characters MUST be avoided or replaced:

| Character   | Where it breaks                                                              | Safe replacement                             |
| ----------- | ---------------------------------------------------------------------------- | -------------------------------------------- |
| `;`         | Sequence message labels (Mermaid 11 statement terminator)                     | `,` or `·` or rephrase                       |
| `\|`        | Flowchart edge labels (Mermaid pipe-delimited edge label syntax)              | `/` or the word "or"                         |
| Backtick    | Mermaid code-span in labels (lexer slices on the first pair)                  | Drop or use single quotes                    |
| `"` (unescaped) | Mermaid label quoting; unmatched double-quote breaks the label parser    | Use `&quot;` in node labels, escape in messages |
| `->`, `-->`, `->>` inside label text | Mermaid arrow tokens; any occurrence in a label confuses the edge scanner | Use `to`, `leads to`, or `→` (UTF-8) |
| Literal newline (`\n` intended as content) | Breaks statement boundaries in both Mermaid and PlantUML     | Use `<br/>` (Mermaid) or `\n` escape (PlantUML) |
| Leading/trailing whitespace in labels | PlantUML trims, Mermaid preserves — inconsistent across renderers | Trim before emitting                         |

Additional rules for sequence diagrams:

- Participant IDs must be valid identifiers: `[A-Za-z_][A-Za-z0-9_]*`. File paths like `csv/export.py` are NOT valid IDs — use an alias: `participant Export as csv/export.py`.
- Message labels should be a single short phrase. If you need a subordinate clause, use a `note over`/`note right of` block instead of stuffing it into the arrow label.

Additional rules for flowcharts (`graph` / `flowchart`):

- Edge labels wrapped in `|...|` cannot themselves contain `|`. Use quoted-label form `-- "label with pipe" -->` if you genuinely need one.
- Node IDs follow the same identifier rule as participants. Put path-shaped or symbol-shaped content in the `[label]`, not the ID.

Additional rules for PlantUML:

- Participant/entity names with spaces or punctuation MUST be double-quoted: `participant "My Service" as MS`.
- Don't use `@startuml`/`@enduml` more than once per block.

## How to apply

Every diagram-emitting skill MUST sanitise labels BEFORE emitting the block. The minimum viable sanitiser:

1. For every string that will land inside a label position (message labels, edge labels, node labels, participant aliases, notes):
   - Replace `;` with `,`.
   - Replace `|` with `/`.
   - Strip backticks.
   - Escape unescaped `"` per the renderer's conventions.
   - Replace literal newlines with `<br/>` (Mermaid) or `\n` (PlantUML).
   - Trim leading and trailing whitespace.
2. For every ID position (participant id, node id), verify the string matches `[A-Za-z_][A-Za-z0-9_]*`. If not, generate an alias (e.g. `P1`, `P2`, ...) and emit `as <original>` if the renderer supports an alias clause.

## Parser validation is the only truth

Sanitisation catches the known classes above. It does not catch everything the parser rejects (diagram-specific syntax rules evolve with Mermaid / PlantUML versions). The only reliable end-to-end check is to run the emitted block through the real parser.

The `pharaoh-diagram-lint` atomic skill does this batch-style over an emitted docs tree. Every diagram-emitting skill's reward criteria SHOULD include a per-emitted-block `mmdc -i tmp.mmd -o /dev/null` (Mermaid) or `plantuml -checkonly tmp.puml` (PlantUML) pass. Sanitisation without parser validation is a false sense of safety.

## Why not move this into a helper?

The sanitisation rules are short and diagram-specific. Hardcoding them inside each emitter's output path keeps the skill atomic (Criterion (e)) — no inter-skill call graph, no shared runtime dependency. If the ruleset grows (e.g. a third renderer lands), extract into a per-language helper then.

# UML relationship semantics cheatsheet

Shared reference for diagram-emitting skills that deal with structural UML diagrams: `pharaoh-class-diagram-draft`, `pharaoh-component-diagram-draft`, `pharaoh-block-diagram-draft`, `pharaoh-feat-component-extract`.

LLMs emitting UML diagrams generally get the syntax right (Mermaid and PlantUML both in training data). They generally get the semantics wrong — every relationship becomes a generic `-->` arrow regardless of whether the concept is composition, aggregation, or a plain use dependency. This cheatsheet gives the minimum rules.

## Relationship types and when to use which

### Composition (strong ownership)
- **Semantics:** The whole OWNS the part. If the whole is destroyed, the part ceases to exist. One part belongs to exactly one whole.
- **Mermaid:** `Whole *-- Part`
- **PlantUML:** `Whole *-- Part`
- **Examples:** Car ↔ Engine (engine lives and dies with the car instance). File system Directory ↔ File entry.

### Aggregation (weak ownership)
- **Semantics:** The whole has a reference to the part but does not own it. Part can outlive the whole. Shared references allowed.
- **Mermaid:** `Whole o-- Part`
- **PlantUML:** `Whole o-- Part`
- **Examples:** University Department ↔ Professor (professor can switch departments). Playlist ↔ Song.

### Association (uses / knows about)
- **Semantics:** A knows about B, can call its methods. No ownership. No lifetime coupling.
- **Mermaid:** `A --> B`
- **PlantUML:** `A --> B` or `A -- B`
- **Examples:** OrderProcessor → PaymentGateway. JamaClient → HttpClient.

### Dependency (transient use)
- **Semantics:** A needs B at some point (parameter, local variable, return type) but does not keep a long-term reference.
- **Mermaid:** `A ..> B`
- **PlantUML:** `A ..> B`
- **Examples:** ReportGenerator ..> PdfSerializer (used once per report). A function taking a logger as a parameter.

### Inheritance (generalization)
- **Semantics:** Subtype is a kind of Supertype. Liskov-substitutable.
- **Mermaid:** `Subtype --|> Supertype`
- **PlantUML:** `Subtype --|> Supertype` (or `Supertype <|-- Subtype`)
- **Examples:** Dog --|> Animal. HTTPError --|> Exception.

### Interface realization (implementation)
- **Semantics:** Concrete class implements abstract interface contract.
- **Mermaid:** `Class ..|> Interface`
- **PlantUML:** `Class ..|> Interface` (or `Interface <|.. Class`)
- **Examples:** ArrayList ..|> List. JamaClient ..|> IRemoteClient.

## Decision matrix

| If the source ...                                       | Use            |
| ------------------------------------------------------- | -------------- |
| owns the target and its lifetime is bound to the source | Composition    |
| has a long-lived reference to the target, which is shared | Aggregation   |
| keeps a long-lived reference to the target              | Association    |
| uses the target transiently (parameter, local)          | Dependency     |
| IS a kind of the target                                 | Inheritance    |
| implements the target's contract                        | Interface realization |

## Common mistakes to avoid

1. **Every arrow as `-->`** — this defaults everything to association, losing ownership / dependency distinctions. Draft skills MUST choose per above.
2. **Composition vs aggregation flipped** — composition is STRONGER (filled diamond, `*--`). Aggregation is WEAKER (hollow diamond, `o--`). "Whole owns part and shares the part's lifetime" is composition. "Whole just references the part" is aggregation.
3. **Inheritance for HAS-A** — inheritance means IS-A. If the source has-a, use composition/aggregation/association, not inheritance.
4. **Mixing directions in PlantUML** — both `Subtype --|> Supertype` and `Supertype <|-- Subtype` are legal in PlantUML. Pick one direction convention per diagram and stick to it.

## Scope

This cheatsheet is for STRUCTURAL UML diagrams only. Sequence, state, activity, use-case, deployment, and fault-tree diagrams have their own grammars — see each draft skill's body for per-type guidance.

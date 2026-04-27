# conditional-present

Same three-branch source function as `conditional-missing/`, but the diagram is authored in PlantUML and wraps the branching behaviour in an `alt` block with two `else` clauses. The grep for `\b(alt|opt|loop|group)\b` at line start matches the `alt` token, so `conditional_branches_marked` passes.

This fixture confirms the detection rule is renderer-agnostic — exact same grep catches the marker whether the diagram is Mermaid (`alt`/`opt`/`loop`) or PlantUML (`alt`/`opt`/`group`).

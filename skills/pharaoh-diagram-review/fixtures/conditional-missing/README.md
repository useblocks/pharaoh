# conditional-missing

Source function `submit_order` carries three conditional branches (`if` / `elif` / `else`) that produce observably different outputs — a `ValueError` on non-positive total, a `ValueError` on missing customer, and a successful acceptance path. The Mermaid sequence diagram presents these as an unconditional linear flow, omitting any `alt` / `opt` / `loop` block.

Detection rule counts `ast.If` (plus `elif`/`else` siblings) in the named function: total >= 2 triggers the grep for `\b(alt|opt|loop|group)\b` against the diagram body. No token is found, so `conditional_branches_marked` fails with the branch count and the missing-marker evidence. The other two new axes are `n/a` (no external imports) or pass (returns go to prior callers).

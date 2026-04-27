# inverted-trigger

Demonstrates the inverted-trigger failure mode. The CREQ asserts the routing happens when `origin_field == "External"`; the source actually branches on `origin_field != "Sphinx-Needs"`. Both the operator (`==` vs `!=`) and the string literal diverge. `trigger_condition_literal_match` fails with evidence naming the divergence. The CREQ's named symbol (`dispatch_item`) does exist in the source, so axis #3 still passes.

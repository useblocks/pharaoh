# unbounded-all

Demonstrates the unbounded-quantifier failure mode. The CREQ says "all validation errors" but the source has thirteen distinct validator functions and the CREQ does not enumerate them. `quantifier_enumerated` fails — the narrow `all + errors` pattern matched, and neither an enumeration colon nor the `namely / specifically / including` markers appear in the same or next sentence. Remediation enumerates the 13 validators by name or splits the CREQ.

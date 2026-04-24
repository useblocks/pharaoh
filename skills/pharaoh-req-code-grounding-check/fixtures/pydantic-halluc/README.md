# pydantic-halluc

Demonstrates the type-framework hallucination failure mode. The CREQ advertises `RowRecord` as a Pydantic model, but the source has `@dataclass` and imports `dataclasses`, not `pydantic`. `type_framework_matches_imports` fails with evidence naming the mismatch. The class name and function both exist in the source, so `named_symbol_exists` passes — the only failure is the false framework claim.

# external-lib-present

Same source file as `external-lib-missing/`, but the diagram declares `participant requests as Requests` — making the external HTTP dependency explicit in the interaction. The participant grep matches `^\s*participant\s+requests\b`, so `external_library_participant` passes.

Note: the `as Requests` alias is the Mermaid / PlantUML display-name syntax; the participant identifier remains `requests`, which is what the grep keys on. Projects that prefer a display alias can set `tailoring.external_alias_map` to accept the alias instead, but the default detection uses the bare import name.

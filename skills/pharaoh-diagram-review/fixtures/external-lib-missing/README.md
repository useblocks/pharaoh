# external-lib-missing

Source function `fetch_report` imports the third-party `requests` library and calls `requests.get(...)` inline. `requests` is not in `sys.stdlib_module_names`, so the detection rule classifies it as external. The Mermaid diagram only lists `CLI` and `WeatherService` as participants and draws the HTTP call as an internal `WeatherService -> WeatherService` step (here elided entirely as a `WeatherService -> CLI` return).

The participant grep `^\s*participant\s+requests\b` finds no match, so `external_library_participant` fails with evidence naming the import site. `conditional_branches_marked` is `n/a` because the source function has no conditional branches; `returns_match_call_stack` passes because the only return goes to `CLI`, which is a prior caller.

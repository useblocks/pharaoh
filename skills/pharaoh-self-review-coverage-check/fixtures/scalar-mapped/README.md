# scalar-mapped

Backward-compatibility fixture for the scalar branch of the detection rule. The emission skill `pharaoh-req-draft` maps to a single string value `pharaoh-req-review`, which is invoked in the emission skill's `## Last step`. Expected output: `passed: true` with an empty `uncovered` list. Proves that extending the map schema to allow list values does not regress existing scalar entries.

# misattributed-config-field

Axis-5 failure case. The CREQ cites three backtick tokens
(`outpath`, `default_format`, `.archive`) that the declared `source_doc`
(the consumer module) does not contain — those names live in the
project's config module and the consumer reaches them only through
attribute access (`self.config.target_path`, `self.config.uuid_target`).

This is a direct replay of an observed dogfooding failure pattern:
authors cite field-default literals when the consumer actually uses
the attribute name, causing a cross-file leak. Axis 5 flags each
token with a retarget hint.

The fixture ships:

- `input-source.py` — the consumer module cited by `:source_doc:`.
- `config/export_config.py` — the schema module carrying the
  default-value literals the CREQ cites.
- `code-grounding-filters.yaml` — enables the
  `cross_file_literal_default` strategy so the skill emits the
  actionable "cite attribute instead / retarget source_doc" evidence
  rather than a generic "not found in source" message.

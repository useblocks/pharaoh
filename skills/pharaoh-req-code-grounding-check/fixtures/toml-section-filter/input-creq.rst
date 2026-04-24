.. comp_req:: Resolve export configuration from TOML
   :id: CREQ_format_cli_commands
   :status: draft
   :source_doc: input-source.py

   The ``to_format`` command shall merge CLI overrides with the
   ``[myapp.to_format]`` section of the project TOML before
   constructing a ``ExportConfig``.

.. comp_req:: Ingest CSV rows honouring caller-chosen delimiter and encoding
   :id: CREQ_csv_import_01
   :status: draft
   :source_doc: input-source.py

   The component shall read the input CSV file using the caller-configured
   column delimiter and text encoding, surfacing a read error to its caller
   when the file cannot be parsed or when the bytes cannot be decoded with
   the configured encoding rather than silently coercing the data.

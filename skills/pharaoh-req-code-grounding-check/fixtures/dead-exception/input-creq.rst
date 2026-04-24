.. comp_req:: Upload client error hierarchy
   :id: CREQ_upload_errors
   :status: draft
   :source_doc: input-source.py

   The upload client shall raise UploadAuthError on authentication failure,
   raise UploadArtifactTypeError on mismatched artefact types, raise
   UploadSkippedValueError on skipped values, raise UploadValueMapError on
   value-map failures, and raise UploadTransportError on transport failures.

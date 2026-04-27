.. comp_req:: Resolve Jama credentials from environment
   :id: CREQ_jama_cli_env_fallback
   :status: draft
   :source_doc: input-source.py

   The CLI shall fall back to ``JAMA_*`` environment variables for
   unset credential fields before failing a ``jama check`` call.

.. comp_req:: Read inventory CSV and emit rows
   :id: CREQ_inventory_read
   :status: draft
   :source_doc: input-source.py

   The component shall call ``read_inventory`` to parse the input file.
   When the ``strict`` flag is set, the component shall raise InventoryValidationError
   on malformed rows. The parser uses the standard ``csv`` module.

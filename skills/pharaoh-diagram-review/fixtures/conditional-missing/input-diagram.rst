.. mermaid::
   :caption: FEAT_order_submit — order submission flow
   :source_doc: input-source.py

   sequenceDiagram
       participant CLI
       participant OrderService
       participant DB

       CLI->>OrderService: submit_order(order)
       OrderService->>DB: persist(order)
       DB-->>OrderService: order_id
       OrderService-->>CLI: OrderAccepted(order_id)

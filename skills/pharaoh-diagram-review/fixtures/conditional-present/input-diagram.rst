.. uml::
   :caption: FEAT_order_submit — order submission flow
   :source_doc: input-source.py

   @startuml
   participant CLI
   participant OrderService
   participant DB

   CLI -> OrderService : submit_order(order)
   alt order.total <= 0
       OrderService --> CLI : ValueError("non-positive total")
   else order.customer_id is None
       OrderService --> CLI : ValueError("missing customer")
   else accepted path
       OrderService -> DB : persist(order)
       DB --> OrderService : order_id
       OrderService --> CLI : OrderAccepted(order_id)
   end
   @enduml

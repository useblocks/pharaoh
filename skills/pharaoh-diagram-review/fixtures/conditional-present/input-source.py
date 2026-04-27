"""Source cited by the diagram's :source_doc: option."""


def submit_order(order, db):
    if order.total <= 0:
        raise ValueError("non-positive total")
    elif order.customer_id is None:
        raise ValueError("missing customer")
    else:
        order_id = db.persist(order)
        return {"status": "accepted", "order_id": order_id}

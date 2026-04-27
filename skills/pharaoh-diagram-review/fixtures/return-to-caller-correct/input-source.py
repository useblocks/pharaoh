"""Source cited by the diagram's :source_doc: option."""


def update_setting(store, key, value):
    store.write(key, value)
    return "updated"

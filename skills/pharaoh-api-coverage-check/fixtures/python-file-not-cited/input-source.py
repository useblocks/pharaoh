"""Cache backend module — behavioral but absent from the catalogue."""


class CacheBackend:
    def get(self, key):
        value = self._storage.get(key)
        if value is None:
            return None
        return value

    def set(self, key, value):
        self._storage[key] = value
        return True

    def __init__(self):
        self._storage = {}


def flush_cache(backend):
    backend._storage.clear()
    return True

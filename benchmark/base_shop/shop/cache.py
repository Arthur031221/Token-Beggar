import time


class PriceCache:
    """Caches price lookups for ttl seconds."""

    def __init__(self, loader, ttl=60, clock=time.monotonic):
        self.loader = loader
        self.ttl = ttl
        self.clock = clock
        self._data = {}

    def get(self, sku: str) -> int:
        hit = self._data.get(sku)
        if hit and self.clock() - hit[1] < self.ttl:
            return hit[0]
        value = self.loader(sku)
        self._data[sku] = (value, self.clock())
        return value

    def invalidate(self, sku: str) -> None:
        self._data.pop(sku, None)

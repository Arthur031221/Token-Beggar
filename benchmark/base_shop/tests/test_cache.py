import unittest

from shop.cache import PriceCache


class CacheTests(unittest.TestCase):
    def test_hit_and_expiry(self):
        now = [0.0]
        calls = []
        cache = PriceCache(lambda sku: calls.append(sku) or 5, ttl=10, clock=lambda: now[0])
        cache.get("x")
        cache.get("x")
        self.assertEqual(len(calls), 1)
        now[0] = 11
        cache.get("x")
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()

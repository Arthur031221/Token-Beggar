import unittest

from shop.models import Cart, Item
from shop.pricing import calc_tax, calc_total


class PricingTests(unittest.TestCase):
    def test_total_with_tax(self):
        cart = Cart()
        cart.add(Item("a", "A", 1000), 2)
        self.assertEqual(calc_total(cart), 2165)

    def test_untaxable_item(self):
        cart = Cart()
        cart.add(Item("b", "B", 500, taxable=False))
        self.assertEqual(calc_total(cart), 500)
        self.assertEqual(calc_tax(cart), 0)

    def test_bulk_discount(self):
        cart = Cart()
        cart.add(Item("c", "C", 100), 10)
        self.assertEqual(calc_total(cart), 1028)


if __name__ == "__main__":
    unittest.main()

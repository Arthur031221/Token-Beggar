import unittest

from shop.models import Cart, Item
from shop.orders import Order
from shop.pricing import calc_total


class OrderTests(unittest.TestCase):
    def make(self):
        cart = Cart(customer="ann")
        cart.add(Item("a", "A", 1000))
        return Order(cart), cart

    def test_total_matches_cart(self):
        order, cart = self.make()
        self.assertEqual(order.total_cents, calc_total(cart))

    def test_state_flow(self):
        order, _ = self.make()
        order.move("paid")
        order.move("shipped")
        with self.assertRaises(ValueError):
            order.move("cancelled")


if __name__ == "__main__":
    unittest.main()

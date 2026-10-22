import itertools

from .pricing import calc_tax, calc_total

_ids = itertools.count(1000)
STATES = ("new", "paid", "shipped", "cancelled")
ALLOWED = {"new": {"paid", "cancelled"}, "paid": {"shipped", "cancelled"}, "shipped": set(), "cancelled": set()}


class Order:
    def __init__(self, cart):
        self.id = next(_ids)
        self.customer = cart.customer
        self.lines = [(l.item.sku, l.qty, l.item.price_cents) for l in cart.lines]
        self.total_cents = calc_total(cart)
        self.tax_cents = calc_tax(cart)
        self.state = "new"

    def move(self, state: str) -> None:
        if state not in ALLOWED[self.state]:
            raise ValueError(f"cannot go from {self.state} to {state}")
        self.state = state

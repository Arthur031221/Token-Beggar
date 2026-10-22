import argparse

from .models import Cart, Item
from .money import fmt, to_cents
from .orders import Order
from .pricing import calc_total
from .reports import render
from .storage import Store


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="shop")
    sub = parser.add_subparsers(dest="cmd", required=True)
    quote = sub.add_parser("quote")
    quote.add_argument("items", nargs="+", help="sku:price:qty")
    report = sub.add_parser("report")
    report.add_argument("--db", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "quote":
        cart = Cart()
        for spec in args.items:
            sku, price, qty = spec.split(":")
            cart.add(Item(sku, sku, to_cents(price)), int(qty))
        print(fmt(calc_total(cart)))
        return 0
    print(render(Store(args.db).load()))
    return 0

from .money import percent

TAX_RATE = 8.25
BULK_THRESHOLD = 10
BULK_DISCOUNT = 5.0


def line_subtotal(line) -> int:
    base = line.item.price_cents * line.qty
    if line.qty >= BULK_THRESHOLD:
        base -= percent(base, BULK_DISCOUNT)
    return base


def calc_total(cart) -> int:
    """Subtotal plus tax in cents."""
    subtotal = sum(line_subtotal(l) for l in cart.lines)
    taxable = sum(line_subtotal(l) for l in cart.lines if l.item.taxable)
    return subtotal + percent(taxable, TAX_RATE)


def calc_tax(cart) -> int:
    taxable = sum(line_subtotal(l) for l in cart.lines if l.item.taxable)
    return percent(taxable, TAX_RATE)

"""Money helpers. All amounts are integer cents."""


def to_cents(amount: str) -> int:
    """'12.34' -> 1234. Accepts at most two decimals."""
    whole, _, frac = amount.partition(".")
    if len(frac) > 2:
        raise ValueError(f"too many decimals: {amount}")
    return int(whole) * 100 + int(frac.ljust(2, "0") or 0)


def fmt(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def percent(cents: int, rate_percent: float) -> int:
    """Round half up, in cents."""
    return int(cents * rate_percent / 100 + 0.5)

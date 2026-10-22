from collections import defaultdict

from .money import fmt


def sales_by_customer(rows: list) -> dict:
    out = defaultdict(int)
    for row in rows:
        if row["state"] in ("paid", "shipped"):
            out[row["customer"]] += row["total"]
    return dict(out)


def render(rows: list) -> str:
    sales = sales_by_customer(rows)
    lines = [f"{name:<12}{fmt(total):>10}" for name, total in sorted(sales.items(), key=lambda kv: -kv[1])]
    return "\n".join(lines)

import json
from pathlib import Path


class Store:
    """Orders as one JSON file."""

    def __init__(self, path):
        self.path = Path(path)

    def load(self) -> list:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def save_order(self, order) -> None:
        rows = [r for r in self.load() if r["id"] != order.id]
        rows.append(
            {"id": order.id, "customer": order.customer, "total": order.total_cents, "tax": order.tax_cents, "state": order.state}
        )
        self.path.write_text(json.dumps(rows, indent=1))

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price_cents: int
    taxable: bool = True


@dataclass
class Line:
    item: Item
    qty: int = 1


@dataclass
class Cart:
    lines: list = field(default_factory=list)
    customer: str = "guest"

    def add(self, item: Item, qty: int = 1) -> None:
        for line in self.lines:
            if line.item.sku == item.sku:
                line.qty += qty
                return
        self.lines.append(Line(item, qty))

    def remove(self, sku: str) -> None:
        self.lines = [l for l in self.lines if l.item.sku != sku]

    def count(self) -> int:
        return sum(l.qty for l in self.lines)

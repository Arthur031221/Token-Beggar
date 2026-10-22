"""The 21 benchmark tasks: three per class. Code tasks are scored by a hidden check script plus the
existing test suite. Answer tasks are scored by a blind judge against a list of required facts."""

from pathlib import Path

import fixture

T = fixture.truth()


def sub(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text()
    assert old in text, (path, old)
    path.write_text(text.replace(old, new, count))


# ---- seeded bugs and review material -------------------------------------------------------------


def seed_to_cents(w: Path) -> None:
    sub(w / "shop/money.py", 'frac.ljust(2, "0")', 'frac.rjust(2, "0")')


def seed_store(w: Path) -> None:
    sub(w / "shop/storage.py", 'if r["id"] != order.id', 'if r["id"] == order.id')


def seed_remove(w: Path) -> None:
    sub(w / "shop/models.py", "l.item.sku != sku", "l.item.name != sku")


def seed_remove_fixture(w: Path) -> None:
    seed_remove(w)
    # make names differ from skus so the bug is visible
    (w / "shop/demo.py").write_text(
        "from .models import Cart, Item\n\nc = Cart()\nc.add(Item('sku-1', 'Widget', 500))\nc.add(Item('sku-2', 'Gadget', 900))\nc.remove('sku-1')\nprint(c.count())\n"
    )


DIFF_ONE = """--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ def line_subtotal(line) -> int:
     base = line.item.price_cents * line.qty
-    if line.qty >= BULK_THRESHOLD:
-        base -= percent(base, BULK_DISCOUNT)
+    if line.qty > BULK_THRESHOLD:
+        base -= percent(base, BULK_DISCOUNT)
     return base
@@ def calc_tax(cart) -> int:
-    taxable = sum(line_subtotal(l) for l in cart.lines if l.item.taxable)
-    return percent(taxable, TAX_RATE)
+    taxable = sum(l.item.price_cents * l.qty for l in cart.lines if l.item.taxable)
+    return percent(taxable, TAX_RATE)
--- a/shop/cache.py
+++ b/shop/cache.py
@@ def get(self, sku: str) -> int:
-        if hit and self.clock() - hit[1] < self.ttl:
+        if hit and self.clock() - hit[1] < self.ttl * 1000:
             return hit[0]
"""
DIFF_ONE_FACTS = [
    "pricing.py: changing >= to > means a line of exactly 10 units no longer gets the bulk discount (off by one at the threshold)",
    "calc_tax now uses the undiscounted price, so tax is charged on the pre-discount amount and disagrees with calc_total",
    "cache.py: ttl multiplied by 1000 makes entries live about 1000 times longer, so the cache serves stale prices (ttl is in seconds)",
]

DIFF_TWO = """--- a/shop/orders.py
+++ b/shop/orders.py
@@ class Order:
-        self.id = next(_ids)
+        self.id = len(_ids_seen)
+        _ids_seen.append(self.id)
@@ def move(self, state: str) -> None:
-        if state not in ALLOWED[self.state]:
+        if state not in ALLOWED.get(self.state, STATES):
             raise ValueError(f"cannot go from {self.state} to {state}")
"""
DIFF_TWO_FACTS = [
    "Order ids derived from len() of a list are not unique or monotonic and the list is appended after reading, so two orders can get the same id (the first id would also collide on restart)",
    "Falling back to STATES in ALLOWED.get(...) allows any transition for an unknown state, which weakens the validation (and every state is allowed, including moving away from cancelled or shipped)",
]

DESIGN_CURRENCY = [
    "Amounts are integer cents everywhere (money.py), so a currency code must travel with every amount; money alone is not enough",
    "Item, Line or Order need a currency field and Store rows need a currency column or key, so saved files need a migration or a default",
    "Rounding and decimal places differ per currency (for example JPY has none), so to_cents, fmt and percent in money.py have to change",
    "Mixed currency carts need a policy: reject them or convert with an exchange rate, and reports.py sums totals so it must not add different currencies together",
]
DESIGN_STORE = [
    "Store.save_order loads and rewrites the whole JSON file on every save, so cost grows with the number of orders",
    "There is no locking or atomic write, so concurrent writers or a crash mid write can lose or corrupt orders",
    "Recommends moving to sqlite (or another real database) with a concrete reason, and keeps the Store interface (load, save_order) so callers do not change",
    "Mentions a migration path for the existing JSON file",
]
DESIGN_CACHE = [
    "PriceCache has no lock, so concurrent get calls can both miss and call the loader twice (a thundering herd) and the dict is mutated unsafely",
    "Expired entries are never evicted, so the dict grows without bound for many skus",
    "Proposes a concrete fix such as a lock per cache or per key, and eviction or a size bound, rather than only saying 'add locking'",
    "Points out that invalidate only removes one sku and gives no way to clear all, or that stale data can be served for up to ttl seconds",
]
READ_FLOW = [
    "orders.py holds the state machine: ALLOWED maps each state to the states it may move to, and Order.move raises ValueError for any other transition",
    "States are new, paid, shipped and cancelled; shipped and cancelled are terminal (no outgoing transitions)",
    "storage.py persists the state string with the order in the JSON file but does not itself validate transitions",
    "reports.py counts only orders in state paid or shipped when summing sales by customer",
]
REVIEW_CARRIERS = [
    f"The {T['grams']} carrier quotes weight in grams (PER_GRAMS, MAX_GRAMS) while every other carrier uses kilograms, so callers passing kg to rate() get wrong prices or a range error",
    "Names which module this is (maple) and that its unit differs from the other carriers",
    "Suggests a fix such as converting units at the registry boundary or standardising the unit in the interface",
]

# ---- hidden checks (python source; exit code 0 means pass) ---------------------------------------

CHK_RENAME = """
import pathlib, subprocess, sys
bad = [str(p) for p in pathlib.Path('.').rglob('*.py') if 'calc_total' in p.read_text()]
assert not bad, bad
from shop.pricing import order_total
from shop.models import Cart, Item
c = Cart(); c.add(Item('a', 'A', 1000), 2)
assert order_total(c) == 2165
"""
CHK_FUTURE = """
import pathlib
files = sorted(pathlib.Path('shop/carriers').glob('*.py'))
assert len(files) == 21
for p in files:
    if p.name == '__init__.py':
        continue
    lines = [l for l in p.read_text().splitlines() if l.strip()]
    code = [l for l in lines if not l.startswith('#') and not l.startswith('\"\"\"')]
    assert 'from __future__ import annotations' in p.read_text(), p
    first_import = next(l for l in lines if l.startswith(('import ', 'from ')))
    assert first_import == 'from __future__ import annotations', (p, first_import)
import shop.carriers
"""
CHK_TODO = """
import pathlib
bad = [str(p) for p in pathlib.Path('shop').rglob('*.py') if 'TODO' in p.read_text()]
assert not bad, bad
import shop.carriers
from shop.carriers import get
assert get('acme').rate(3) > 0
"""
CHK_COUPON = """
from shop.models import Cart, Item
from shop.pricing import calc_total
c = Cart(); c.add(Item('a', 'A', 1000, taxable=False), 2)
assert calc_total(c) == 2000
c.apply_coupon('SAVE10')
assert calc_total(c) == 1800
c.apply_coupon('FLAT500')
assert calc_total(c) == 1300, calc_total(c)
try:
    c.apply_coupon('NOPE'); raise SystemExit('unknown coupon accepted')
except ValueError:
    pass
"""
CHK_SPLIT = """
from shop.money import split
assert split(100, 3) == [34, 33, 33]
assert split(10, 5) == [2, 2, 2, 2, 2]
assert sum(split(1001, 7)) == 1001
assert split(0, 3) == [0, 0, 0]
try:
    split(5, 0); raise SystemExit('zero parts accepted')
except ValueError:
    pass
"""
CHK_JSON = """
import io, json, contextlib
from shop.cli import main
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    code = main(['quote', '--json', 'a:10.00:2'])
assert code == 0
data = json.loads(buf.getvalue())
assert data == {'total_cents': 2165}, data
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    main(['quote', 'a:10.00:2'])
assert buf.getvalue().strip() == '21.65'
"""
CHK_SHIPPING = """
from shop.models import Cart, Item
from shop.orders import Order
from shop.storage import Store
from shop.reports import render
import tempfile, os, json
c = Cart(customer='ann'); c.add(Item('a', 'A', 1000, taxable=False), 2)
o = Order(c, carrier='acme', weight=3, zone='local')
from shop.carriers import get
expected = get('acme').rate(3, 'local')
assert o.shipping_cents == expected, (o.shipping_cents, expected)
assert o.total_cents == 2000 + expected, o.total_cents
d = tempfile.mkdtemp(); s = Store(os.path.join(d, 'db.json'))
o.move('paid'); s.save_order(o)
row = s.load()[0]
assert row['shipping'] == expected, row
out = render(s.load())
assert 'ann' in out
o2 = Order(c); assert o2.shipping_cents == 0
"""
CHK_REFUND = """
from shop.models import Cart, Item
from shop.orders import Order
from shop.storage import Store
from shop.reports import sales_by_customer
import tempfile, os
c = Cart(customer='bob'); c.add(Item('a', 'A', 1000, taxable=False))
o = Order(c); o.move('paid'); o.move('refunded')
assert o.state == 'refunded'
try:
    o.move('shipped'); raise SystemExit('refunded -> shipped allowed')
except ValueError:
    pass
o2 = Order(c); o2.move('paid'); o2.move('shipped'); o2.move('refunded')
o3 = Order(c); o3.move('paid')
d = tempfile.mkdtemp(); s = Store(os.path.join(d, 'db.json'))
for x in (o, o2, o3):
    s.save_order(x)
assert sales_by_customer(s.load()) == {'bob': 1000}, sales_by_customer(s.load())
"""
CHK_TIER = """
from shop.models import Cart, Item
from shop.pricing import calc_total
import io, contextlib
from shop.cli import main
c = Cart(); c.add(Item('a', 'A', 1000, taxable=False), 2)
assert calc_total(c) == 2000
c.tier = 'gold'
assert calc_total(c) == 1800, calc_total(c)
c.tier = 'silver'
assert calc_total(c) == 1900, calc_total(c)
c.tier = 'unknown'
assert calc_total(c) == 2000
from shop.orders import Order
c.tier = 'gold'
assert Order(c).total_cents == 1800
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    main(['quote', '--tier', 'gold', 'a:10.00:2'])
assert buf.getvalue().strip() == '19.49', buf.getvalue()
"""
CHK_TO_CENTS = """
from shop.money import to_cents
assert to_cents('12.5') == 1250
assert to_cents('12.05') == 1205
assert to_cents('7') == 700
import io, contextlib
from shop.cli import main
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    main(['quote', 'a:12.5:2'])
assert buf.getvalue().strip() == '27.06', buf.getvalue()
"""
CHK_STORE = """
from shop.models import Cart, Item
from shop.orders import Order
from shop.storage import Store
import tempfile, os
d = tempfile.mkdtemp(); s = Store(os.path.join(d, 'db.json'))
c = Cart(customer='x'); c.add(Item('a', 'A', 100))
a, b = Order(c), Order(c)
s.save_order(a); s.save_order(b)
assert len(s.load()) == 2
a.move('paid'); s.save_order(a)
rows = s.load()
assert len(rows) == 2 and {r['id']: r['state'] for r in rows}[a.id] == 'paid'
"""
CHK_REMOVE = """
from shop.models import Cart, Item
c = Cart(); c.add(Item('sku-1', 'Widget', 500)); c.add(Item('sku-2', 'Gadget', 900))
c.remove('sku-1')
assert c.count() == 1 and c.lines[0].item.sku == 'sku-2'
"""


def task(id, cls, prompt, check=None, facts=None, setup=None, needs_tests=True):
    return {"id": id, "class": cls, "prompt": prompt, "check": check, "facts": facts, "setup": setup, "tests": needs_tests}


def seed_all_carriers(w: Path) -> None:
    pass


def diff_file(text: str):
    def setup(w: Path) -> None:
        (w / "change.diff").write_text(text)

    return setup


TASKS = [
    # mechanical
    task(
        "m1-rename",
        "mechanical",
        "Rename the function calc_total to order_total everywhere in this repo (code and tests). Run the tests when done.",
        CHK_RENAME,
    ),
    task(
        "m2-future",
        "mechanical",
        "Add the line `from __future__ import annotations` as the first import in every module under shop/carriers/ except __init__.py. Keep everything else unchanged and run the tests.",
        CHK_FUTURE,
    ),
    task("m3-todo", "mechanical", "Delete every `# TODO(...)` comment line anywhere under shop/. Change nothing else. Run the tests.", CHK_TODO),
    # reading
    task(
        "r1-tracking",
        "reading",
        "Which carriers in shop/carriers/ do not provide a tracking_url method? Answer with the carrier names only, as a comma separated list.",
        facts=["The answer lists exactly these carriers: " + ", ".join(T["no_tracking"]) + " (no extra names, none missing)"],
        needs_tests=False,
    ),
    task(
        "r2-toprate",
        "reading",
        "Which carrier has the highest BASE_RATE, and what is it? Answer in one sentence.",
        facts=[f"Names {T['top_rate'][0]} as the highest, with BASE_RATE {T['top_rate'][1]}"],
        needs_tests=False,
    ),
    task(
        "r3-flow",
        "reading",
        "Explain how order state changes are validated and stored in this repo. Name the files and functions involved. Under 200 words.",
        facts=READ_FLOW,
        needs_tests=False,
    ),
    # routine code
    task(
        "c1-coupon",
        "routine_code",
        "Add Cart.apply_coupon(code). Coupons live in a new module shop/coupons.py: SAVE10 takes 10 percent off the subtotal, FLAT500 takes 500 cents off. Coupons stack, apply to the pre tax subtotal, and an unknown code raises ValueError. calc_total must reflect them. Add a test and run the tests.",
        CHK_COUPON,
    ),
    task(
        "c2-split",
        "routine_code",
        "Add split(cents, parts) to shop/money.py. It returns a list of `parts` integers summing to cents, with the remainder spread one cent at a time from the first element. parts below 1 raises ValueError. Add a test and run the tests.",
        CHK_SPLIT,
    ),
    task(
        "c3-json",
        "routine_code",
        'Add a --json flag to the `quote` command in shop/cli.py that prints {"total_cents": N} as JSON instead of the formatted amount. Keep the default output unchanged. Add a test and run the tests.',
        CHK_JSON,
    ),
    # multi file
    task(
        "f1-shipping",
        "multi_file",
        "Add shipping to orders. Order(cart, carrier=None, weight=0, zone='local') computes shipping_cents from the carrier registry in shop/carriers (0 when no carrier), total_cents includes it, Store.save_order persists it as 'shipping', and the report in shop/reports.py keeps working. Add tests and run them.",
        CHK_SHIPPING,
    ),
    task(
        "f2-refund",
        "multi_file",
        "Add a 'refunded' order state. paid and shipped orders can move to refunded, refunded is terminal, and refunded orders must not count in sales_by_customer. Update every place that needs it and add tests. Run the tests.",
        CHK_REFUND,
    ),
    task(
        "f3-tier",
        "multi_file",
        "Add customer tiers. Cart gets a `tier` attribute (default 'standard'). gold takes 10 percent off the subtotal, silver 5 percent, any other value nothing. The discount applies before tax, in calc_total and the tax calculation, and Order must pick it up. Add a `--tier` option to the quote command. Add tests and run them.",
        CHK_TIER,
    ),
    # debugging
    task(
        "d1-cents",
        "debugging",
        "`python3 -m shop quote a:12.5:2` is wrong: it should print 27.06 but prints something else. (Run it as `python3 -c \"from shop.cli import main; main(['quote','a:12.5:2'])\"` if there is no __main__.) Find the root cause and fix it. Run the tests.",
        CHK_TO_CENTS,
        setup=seed_to_cents,
    ),
    task(
        "d2-store",
        "debugging",
        "After saving two different orders with Store.save_order, Store.load() returns only one of them. Find the root cause and fix it. Run the tests.",
        CHK_STORE,
        setup=seed_store,
    ),
    task(
        "d3-remove",
        "debugging",
        "Cart.remove('sku-1') does not remove the Widget line, see shop/demo.py. Find the root cause and fix it. Run the tests.",
        CHK_REMOVE,
        setup=seed_remove_fixture,
    ),
    # design
    task(
        "g1-currency",
        "design",
        "We want to support multiple currencies in this repo. Do not write code. Give me a design: what has to change, in which files, and the main risks. Under 250 words.",
        facts=DESIGN_CURRENCY,
        needs_tests=False,
    ),
    task(
        "g2-store",
        "design",
        "Orders are stored by shop/storage.py. We expect 100k orders and two writer processes. Do not write code. Recommend what to do and why, with a migration path. Under 250 words.",
        facts=DESIGN_STORE,
        needs_tests=False,
    ),
    task(
        "g3-cache",
        "design",
        "Review shop/cache.py for use from many threads in a long running service. Do not write code. List the problems you see and the fix you would choose. Under 250 words.",
        facts=DESIGN_CACHE,
        needs_tests=False,
    ),
    # review
    task(
        "v1-diff",
        "review",
        "Review the change in change.diff against this repo. List every bug it introduces and why. Do not edit files.",
        facts=DIFF_ONE_FACTS,
        setup=diff_file(DIFF_ONE),
        needs_tests=False,
    ),
    task(
        "v2-diff",
        "review",
        "Review the change in change.diff against this repo. List every bug it introduces and why. Do not edit files.",
        facts=DIFF_TWO_FACTS,
        setup=diff_file(DIFF_TWO),
        needs_tests=False,
    ),
    task(
        "v3-carriers",
        "review",
        "Read the modules in shop/carriers/ and report any inconsistency between carriers that would break callers of the registry. Name the module. Do not edit files.",
        facts=REVIEW_CARRIERS,
        needs_tests=False,
    ),
]

assert len(TASKS) == 21 and len({t["id"] for t in TASKS}) == 21

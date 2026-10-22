"""Builds the working copy a benchmark task runs in: the base shop plus 20 generated carrier modules.

Everything is deterministic, so the ground truth for the reading tasks is computed here, not typed by hand.
"""

import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
NAMES = [
    "acme",
    "borealis",
    "cedar",
    "delta",
    "ember",
    "fjord",
    "gale",
    "harbor",
    "iris",
    "juniper",
    "kestrel",
    "lumen",
    "maple",
    "nimbus",
    "onyx",
    "prairie",
    "quartz",
    "ridge",
    "summit",
    "tundra",
]
NO_TRACKING = {"delta", "kestrel", "onyx", "tundra"}
GRAMS = "maple"  # the one carrier that quotes by grams


def base_rate(i: int) -> int:
    return 450 + (i * 37) % 400 + (i % 3) * 25


def carrier_source(i: int, name: str) -> str:
    cls = name.capitalize()
    unit = "grams" if name == GRAMS else "kg"
    per = 3 if name == GRAMS else 310 + (i * 13) % 90
    tracking = (
        ""
        if name in NO_TRACKING
        else f"""
    def tracking_url(self, code: str) -> str:
        return f"https://track.{name}.example/t/{{code}}"
"""
    )
    todo = f"# TODO(owner-{i % 4}): confirm zone table with {name} account manager\n"
    return f'''{todo}"""{cls} Freight rate card. Quotes in cents, weight in {unit}."""

import re

CARRIER = "{name}"
BASE_RATE = {base_rate(i)}
PER_{unit.upper()} = {per}
ZONES = {{"local": 1.0, "regional": 1.{i % 5 + 1}, "national": 1.{i % 4 + 6}}}
MAX_{unit.upper()} = {30000 if name == GRAMS else 30 + i}


class {cls}Carrier:
    name = CARRIER

    def rate(self, weight: float, zone: str = "local") -> int:
        if weight <= 0 or weight > MAX_{unit.upper()}:
            raise ValueError("weight out of range for {name}")
        factor = ZONES[zone]
        return int((BASE_RATE + PER_{unit.upper()} * weight) * factor)

    def label(self, order_id: int) -> str:
        return f"{name.upper()}-{{order_id:08d}}"

    def valid_label(self, text: str) -> bool:
        return re.fullmatch(r"{name.upper()}-\\d{{8}}", text) is not None
{tracking}'''


def registry_source() -> str:
    imports = "\n".join(f"from .{n} import {n.capitalize()}Carrier" for n in NAMES)
    entries = ",\n".join(f'    "{n}": {n.capitalize()}Carrier()' for n in NAMES)
    return f'"""Carrier registry."""\n\n{imports}\n\nREGISTRY = {{\n{entries},\n}}\n\n\ndef get(name: str):\n    return REGISTRY[name]\n'


def build(dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(HERE / "base_shop", dest, ignore=shutil.ignore_patterns("__pycache__"))
    pkg = dest / "shop" / "carriers"
    pkg.mkdir()
    for i, name in enumerate(NAMES):
        (pkg / f"{name}.py").write_text(carrier_source(i, name))
    (pkg / "__init__.py").write_text(registry_source())
    (dest / "README.md").write_text("# shop\n\nSmall order and pricing library. Run tests with `python3 -m unittest discover -s tests -t .`\n")
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True)
    subprocess.run(["git", "-c", "user.name=bench", "-c", "user.email=b@b", "commit", "-qm", "base"], cwd=dest, check=True)
    return dest


def truth() -> dict:
    rates = {n: base_rate(i) for i, n in enumerate(NAMES)}
    top = max(rates, key=rates.get)
    return {"no_tracking": sorted(NO_TRACKING), "rates": rates, "top_rate": (top, rates[top]), "grams": GRAMS}


if __name__ == "__main__":
    import sys

    print(build(Path(sys.argv[1])))

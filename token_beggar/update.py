"""Refresh the model catalog from Anthropic's public models page. Stdlib only."""

import json
import re
import time
import urllib.request

from . import catalog, paths

URL = "https://platform.claude.com/docs/en/about-claude/models/overview.md"
REFRESH_SECONDS = 7 * 24 * 3600


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _tokens(cell: str) -> int:
    """'1M tokens' or '200k tokens'. A model whose window is not stated gets the 1M every current model has."""
    match = re.search(r"([\d.]+)\s*([KkMm])", cell)
    if not match:
        return 1_000_000
    return int(float(match.group(1)) * (1_000_000 if match.group(2).lower() == "m" else 1_000))


def parse_overview(markdown: str) -> list[dict]:
    """Read the 'Compare models' table: one column per current model."""
    rows = {}
    header = None
    for line in markdown.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if cells[0] == "Feature":
            header = cells[1:]
        elif cells[0] == "Claude API ID":
            rows["id"] = cells[1:]
        elif "Default effort" in cells[0]:
            rows["effort"] = cells[1:]
        elif cells[0].startswith("[Context window]") or cells[0] == "Context window":
            rows["window"] = cells[1:]
        elif "Pricing" in cells[0]:
            rows["price"] = cells[1:]
    if not header or not {"id", "price"} <= rows.keys():
        return []
    found = []
    for index, title in enumerate(header):
        name = re.search(r"Claude (\w+) [\d.]+", title)
        model_id = re.search(r"`(claude-[\w-]+)`", rows["id"][index])
        prices = re.search(r"\$([\d.]+) / input MTok, (?:From )?\$([\d.]+) / output MTok", rows["price"][index].replace("From $", "$"))
        if not (name and model_id and prices):
            continue
        effort = re.search(r"`(\w+)`", rows.get("effort", [""] * len(header))[index])
        found.append(
            {
                "alias": name.group(1).lower(),
                "id": model_id.group(1),
                "input_per_mtok": float(prices.group(1)),
                "output_per_mtok": float(prices.group(2)),
                "default_effort": effort.group(1) if effort else "high",
                "context_window": _tokens(rows.get("window", [""] * len(header))[index]),
            }
        )
    found.sort(key=lambda m: m["input_per_mtok"])
    for tier, model in enumerate(found, start=1):
        model["tier"] = tier
    return found


def fetch(timeout: float = 15.0) -> str:
    request = urllib.request.Request(URL, headers={"Accept": "text/markdown", "User-Agent": "token-beggar"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def merged(found: list[dict]) -> dict:
    base = catalog.load()
    known = {row["id"]: row for row in base.get("claude", [])}
    for row in found:  # the overview page has no cache prices: keep the ones already known while the input price is unchanged
        old = known.get(row["id"])
        if old and old.get("input_per_mtok") == row["input_per_mtok"]:
            for key in ("cache_read_per_mtok", "cache_write_per_mtok"):
                if key in old:
                    row[key] = old[key]
    return {**base, "updated": time.strftime("%Y-%m-%d"), "claude": found}


def refresh(target=None, markdown: str | None = None) -> dict:
    found = parse_overview(markdown if markdown is not None else fetch())
    if len(found) < 2:
        raise ValueError("the models page no longer parses: keeping the current catalog")
    data = merged(found)
    (target or paths.home() / "models.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def due() -> bool:
    stamp = paths.home() / "models.checked"
    try:
        return time.time() - float(stamp.read_text()) > REFRESH_SECONDS
    except (OSError, ValueError):
        return True


def mark_checked() -> None:
    (paths.home() / "models.checked").write_text(str(time.time()))

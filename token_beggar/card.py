"""The routing card injected into the model's context: a menu of every available combination and the rules for choosing."""

from . import catalog, paths, profiles

MARKER = "Token Beggar is on."


def command() -> str:
    return str(paths.PACKAGE_ROOT / "bin" / "token-beggar")


def unavailable(inventory: dict) -> set[str]:
    """Aliases and tool keys that are denied or out of quota right now."""
    gone = {m.alias for m in catalog.models()} - set(inventory.get("claude", []))
    return gone | profiles.exhausted(inventory)


def menu(ceiling: dict, inventory: dict, caps: dict | None = None) -> dict:
    gone = unavailable(inventory)
    top = catalog.find(ceiling.get("model"))
    return {
        "claude": profiles.claude_combos(ceiling, gone),
        "external": profiles.external_combos(inventory, caps or {}, gone, top.tier if top else None),
        "unavailable": sorted(a for a in gone if not (top and (m := catalog.find(a)) and m.tier > top.tier)),
        "caps": caps or {},
    }


def _claude_lines(combos: list[dict], known: bool) -> list[str]:
    spec = profiles.load()["claude"]
    by_model: dict[str, list[dict]] = {}
    for row in combos:
        by_model.setdefault(row["model"], []).append(row)
    lines = []
    for alias, rows in by_model.items():
        efforts = "|".join(r["effort"] for r in rows)
        info = spec.get(alias, {})
        lines.append(
            f"- claude {alias} (cap {rows[0]['capability']}, ${rows[0]['price_out']:g}/Mtok out, effort {efforts}): "
            f"{info.get('good_for', '')}. Weak: {info.get('weak_at', '')}."
        )
    return lines


def _external_lines(rows: list[dict], inventory: dict) -> list[str]:
    spec = profiles.load()["external"]
    by_tool: dict[str, list[dict]] = {}
    for row in rows:
        by_tool.setdefault(row["provider"], []).append(row)
    lines = []
    for tool in inventory.get("external", []):
        name = tool["name"]
        if tool.get("kind") == "mcp":
            lines.append(f"- {name} (MCP server): call its tools directly for bulk reading or a second opinion. Check what comes back.")
            continue
        models = by_tool.get(name)
        if not models:
            continue
        info = spec.get(name, {})
        listing = ", ".join(f"{m['model']} (capability {m['capability']})" for m in models)
        lines.append(f"- {name}: {listing}. Good for: {info.get('good_for', '')}. Weak at: {info.get('weak_at', '')}.")
    return lines


def build(ceiling: dict, inventory: dict, caps: dict | None = None) -> str:
    options = menu(ceiling, inventory, caps)
    top = ceiling["model"] or "the model of this chat"
    lines = [
        f"{MARKER} Ceiling for this session: {top} at {ceiling['effort']} effort. Never use a Claude model or effort above it.",
        "Pick the cheapest route below that does each subtask right. "
        "Delegate before you read anything: reading it yourself and then handing it over pays twice.",
        "Menu:",
    ]
    if not ceiling["known"]:
        lines.append("(ceiling model unknown: use only models at or below your own)")
    lines += _claude_lines(options["claude"], ceiling["known"])
    outside = _external_lines(options["external"], inventory)
    if outside:
        lines.append(
            "External AIs use their own quota, not your Claude quota. Their output is a draft: Claude checks it, "
            "and judgement and the final answer stay with Claude. "
            f'Call one with: {command()} ask <tool> [--model <id>] [--file <path> ...] "<the whole task>". Never send secrets.'
        )
        lines += outside
    if options["caps"]:
        lines.append("User caps for this session: " + ", ".join(f"{t} {c}" for t, c in options["caps"].items()) + ". Honour them.")
    lines.append("Rules:")
    lines += [f"- {rule}" for rule in profiles.rules()]
    if outside:
        lines += [f"- {rule}" for rule in profiles.external_rules()]
    lines.append(
        "Workers: Agent tool, subagent_type 'token-beggar:beggar-worker', model and effort set on the call. Independent ones go in one message. "
        "Give the goal, exact paths, the check to run and 'report under 150 words'. When they return, answer; do not re-read what they changed."
    )
    if options["unavailable"]:
        lines.append(f"Out of quota or blocked right now: {', '.join(options['unavailable'])}. They are left off the menu.")
    lines.append("A one-line footer with the quota and money saved is added for you at the end of the turn. Do not write one.")
    return "\n".join(lines)


def lean(ceiling: dict, inventory: dict) -> str:
    """The one line card for a ceiling where the measured saving is about even overall: only multi-file work leaves the chat."""
    top = catalog.find(ceiling.get("model"))
    gone = unavailable(inventory)
    lower = [m for m in catalog.models() if top and m.tier < top.tier and m.alias not in gone]
    pick = lower[-1] if lower else top
    effort = catalog.cap_effort("medium", ceiling["effort"])
    where = f"model {pick.alias}, effort {effort}" if pick else "a model no higher than your own"
    return (
        f"{MARKER} Work inline. The one exception: a change that spans three or more files goes to ONE token-beggar:beggar-worker "
        f"Agent call as your first action ({where}), with the goal, exact paths, the check to run and 'report under 150 words'. "
        "Then answer from its report without re-reading what it changed. A one-line footer is added for you. Do not write one."
    )


def reminder() -> str:
    return "Token Beggar: split this prompt into subtasks and pick each route from the menu given earlier in this session."

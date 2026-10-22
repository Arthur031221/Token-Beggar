"""The routing card injected into the model's context: a menu of every available combination and the rules for choosing."""

from . import catalog, footer, paths, profiles

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
    lines.append("A one-line footer with the quota and money saved is added for you at the end of the turn. Do not write one." + effort_tip(ceiling))
    return "\n".join(lines)


GROW_STEPS = 5  # tool calls in one reply after which a task that started small is treated as large
GROW_CONTEXT = 80_000  # or a main context this long: every later turn re-reads what the chat model has already read


def effort_tip(ceiling: dict) -> str:
    """At max effort a small task costs several times what it does at medium. The skill cannot change the chat's effort, so it can only say so."""
    cost = footer.effort_cost()
    if ceiling.get("effort") != "max" or not cost.get("max") or not cost.get("medium"):
        return ""
    return (
        " The chat runs at max effort. If this task is small, tell the user in one line that a lower effort would do it for much less "
        f"(small tasks cost about {cost['max'] / cost['medium']:.1f}x as much at max as at medium) and carry on."
    )


def _worker_pick(ceiling: dict, inventory: dict) -> str:
    top = catalog.find(ceiling.get("model"))
    gone = unavailable(inventory)
    lower = [m for m in catalog.models() if top and m.tier < top.tier and m.alias not in gone]
    pick = lower[-1] if lower else top
    effort = catalog.cap_effort("medium", ceiling["effort"])
    return f"model {pick.alias}, effort {effort}" if pick else "a model no higher than your own"


def sized(ceiling: dict, inventory: dict) -> str:
    """The short card for a ceiling where small tasks are not worth a worker: decide by the size of the task first."""
    outside = " ".join(
        [
            f"Use {tool['name']} only if the user names it or one job reads about 100k tokens or more: "
            f'{command()} ask <tool> [--file <path> ...] "<the whole task>". Never send secrets.'
            for tool in inventory.get("external", [])[:1]
        ]
    )
    return (
        f"{MARKER} Size the task before you read any code. "
        "LARGE if any of these hold: the prompt is an issue or a bug to fix in a repository you have not read this session, you expect more than "
        f"about {GROW_STEPS} tool calls, it touches more than one file, or it needs an edit and test loop. If unsure, it is LARGE. "
        "SMALL only for a one-shot answer or an edit to one named file: do it inline, dispatch nothing. "
        f"LARGE: send ONE token-beggar:beggar-worker Agent call ({_worker_pick(ceiling, inventory)}) the reproduce, explore, fix and "
        "run-the-tests steps as a numbered list, with the goal, exact paths and the check to run. "
        "It reports under 150 words: root cause, files changed, the test command and the last lines of its output. "
        "Before you answer you must yourself read the whole `git diff` (the diff, not the files), run the target test and the tests of that module, "
        "and check that the root cause matches the diff. If a test fails or they do not match, send one follow-up worker with the failure, "
        "or fix it inline if it takes about 3 steps. Independent jobs go out in one message. "
        "You keep the plan, the root cause, design trade-offs and the answer. "
        f"If a small task grows past about {GROW_STEPS} steps, switch to this for the rest. "
        + (outside + " " if outside else "")
        + "A one-line footer is added for you after a large task. Do not write one."
        + effort_tip(ceiling)
    )


def grown() -> str:
    """Said once in a reply that has passed the step or context limit without a worker."""
    return (
        f"Token Beggar: this task is no longer small (more than {GROW_STEPS} steps, or a long context). Dispatch the rest now: one "
        "token-beggar:beggar-worker Agent call with the goal, exact paths, the check to run and 'report under 150 words'. "
        "Keep the plan and the root cause, and before you answer read the whole `git diff` and run the tests yourself."
    )


def reminder() -> str:
    return "Token Beggar: split this prompt into subtasks and pick each route from the menu given earlier in this session."

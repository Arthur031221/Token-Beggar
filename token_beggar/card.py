"""The routing card injected into the model's context, built for this session's ceiling."""

import json

from . import catalog, paths, routes

MARKER = "Token Beggar is on."
MIN_CLAIM = 1.15  # below this the benchmark cannot tell a saving from run to run spread


def measured() -> dict | None:
    try:
        return json.loads(paths.data_file("measured.json").read_text()).get("benchmark")
    except (OSError, json.JSONDecodeError):
        return None


def footer_rule(ceiling: dict) -> str:
    """Numbers come from the committed benchmark and only apply to the model and effort it was run on."""
    bench = measured()
    stated = ceiling.get("effort_source", "default") != "default"  # an effort we only guessed is not a match
    if bench and bench.get("classes") and stated and ceiling.get("model") == bench["top_model"] and ceiling["effort"] == bench["top_effort"]:
        per_class = {c: v["cost_x"] for c, v in bench["classes"].items() if v.get("cost_x", 0) >= MIN_CLAIM}
        table = ", ".join(f"{c} {x}x" for c, x in per_class.items())
        return (
            "After a reply where you handed work to a cheaper model, end it with one line: "
            "'Token Beggar: about <X>x less spend than "
            f"{bench['top_model']} {bench['top_effort']} alone (measured, <class>)'. "
            f"Use X from this table only, by the class of the task you routed: {table}. "
            "Never write a multiplier that is not in that table. "
            "If the class is not listed, write 'Token Beggar: routed <n> subtask(s) to <model list>' with no number. "
            "If a task mixed classes, use the lowest X. If you routed nothing, add no line."
        )
    return (
        "After a reply where you handed work to a cheaper model, end it with one line: "
        "'Token Beggar: routed <n> subtask(s) to <model list>'. Give no multiplier: "
        "the benchmark was not run on this model and effort."
    )


def build(ceiling: dict, inventory: dict) -> str:
    unavailable = {m.alias for m in catalog.models()} - set(inventory.get("claude", []))
    unavailable |= {a for a, until in (inventory.get("exhausted") or {}).items() if until > __import__("time").time()}
    top = ceiling["model"] or "the model of this chat"
    lines = [
        f"{MARKER} Ceiling for this session: {top} at {ceiling['effort']} effort. Never route above it.",
        "Grade the task before you read a file or run a command. Rows marked Agent subagent go to a worker as your FIRST action: "
        "the worker does the reading, editing and testing in its own context, so do not explore first.",
        "Stay inline for chat, one-line answers, judgement rows, and anything that takes under about three tool calls.",
        "class | model | effort | how",
    ]
    if ceiling["known"]:
        for row in routes.table(ceiling, unavailable):
            how = "stay inline" if row["mode"] == "inline" else "Agent subagent"
            lines.append(f"{row['class']} | {row['model']} | {row['effort']} | {how}")
    else:
        lines.append("(ceiling model unknown: use the table in the token-beggar skill, never above your own model)")
    lines += [
        "Dispatch with the Agent tool: subagent_type 'token-beggar:beggar-worker', model and effort set per call, "
        "run_in_background false so you get the result before you continue. "
        "Put the whole task, the paths or search terms and the check to run in the prompt, and ask for a result under 150 words. "
        "Then verify with one command (the test run or git diff --stat), not by re-reading the files. "
        "Design, root-cause judgement and the final answer stay with you.",
    ]
    if unavailable:
        lines.append(f"Out of quota or blocked right now: {', '.join(sorted(unavailable))}. The router already skips them.")
    external = [e["name"] for e in inventory.get("external", [])]
    if external:
        lines.append(f"Other AIs on this machine: {', '.join(external)}. Not bound by the ceiling unless the user caps them.")
    lines.append(footer_rule(ceiling))
    return "\n".join(lines)


def reminder() -> str:
    return "Token Beggar: grade this task and route it with the table from earlier in this session."

"""Command line: `python3 -m token_beggar <command>`."""

import argparse
import json
import os
import sys

from . import (
    __version__,
    card,
    catalog,
    ceiling,
    compact,
    doctor,
    external,
    footer,
    handoff,
    hooks,
    inventory,
    paths,
    stats,
    transcript,
    update,
    usage,
)


def _session_id(args: argparse.Namespace) -> str | None:
    return getattr(args, "session", None) or os.environ.get("CLAUDE_CODE_SESSION_ID")


def _cmd_menu(args: argparse.Namespace) -> int:
    top = ceiling.resolve(None, None)
    if args.model:
        top = {**top, "model": catalog.find(args.model).id, "known": True}
    if args.effort:
        top["effort"] = args.effort
    options = card.menu(top, inventory.load(), external.load_caps(_session_id(args)))
    if args.json:
        print(json.dumps({"ceiling": top, **options}, indent=2))
        return 0
    print(f"ceiling: {top['model'] or 'unknown'} at {top['effort']}")
    for row in options["claude"]:
        print(f"claude {row['model']:<7} {row['effort']:<7} capability {row['capability']}  cost index {row['cost_index']:g}")
    for row in options["external"]:
        print(f"{row['provider']:<7} {row['model']:<28} capability {row['capability']}  own quota, not Claude's")
    if options["unavailable"]:
        print("unavailable:", ", ".join(options["unavailable"]))
    return 0


def _cmd_mode(args: argparse.Namespace) -> int:
    """How much the skill acts for a ceiling, and the measured ratio behind it."""
    pool = footer.pooled()
    if args.all:
        print(f"{'model':<10}" + "".join(f"{e:<16}" for e in catalog.EFFORTS))
        for model in sorted((m for m in catalog.models() if footer.overall(m.id, "high")), key=lambda m: -m.tier):
            cells = [f"{footer.mode(model.id, e, pool=pool)} {footer.overall(model.id, e):.2f}x" for e in catalog.EFFORTS]
            print(f"{model.alias:<10}" + "".join(f"{c:<16}" for c in cells))
        return 0
    top = ceiling.resolve(None, None)
    model = catalog.find(args.model) if args.model else catalog.find(top["model"])
    effort = args.effort or top["effort"]
    ratio = footer.overall(model.id, effort) if model else None
    shown = footer.mode(model.id if model else None, effort, pool=pool)
    name = model.alias if model else "unknown model"
    print(f"{name} {effort}: {shown}" + (f" (measured cost alone over with the skill: {ratio:.2f}x)" if ratio else " (not measured)"))
    return 0


def _cmd_note(args: argparse.Namespace) -> int:
    session_id = _session_id(args)
    if not session_id:
        print("no session id: pass --session or run this from a Claude Code session", file=sys.stderr)
        return 2
    text = " ".join(args.text) if args.text else sys.stdin.read()
    if not text.strip():
        print("the note is empty", file=sys.stderr)
        return 2
    found = usage.find_transcript(session_id)
    used = transcript.tail_context_tokens(found) if found else 0
    if args.progress is not None and not 0 <= args.progress <= 1:
        print("--progress is a fraction from 0 to 1", file=sys.stderr)
        return 2
    handoff.write_model(
        session_id, text, mid_step=args.mid_step, used=used, progress=args.progress, phase_done=args.phase_done, needs_detail=args.needs_early_detail
    )
    kind = "mid-step" if args.mid_step else "phase done" if args.phase_done else "clean"
    print(f"note saved ({kind}, context {used // 1000}k)")
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    result = external.ask(args.tool, " ".join(args.task), args.model, args.file, _session_id(args))
    if result["ok"]:
        print(result["text"])
        print(f"[{args.tool}: ran on its own quota, not Claude's]", file=sys.stderr)
        return 0
    print(f"{args.tool} failed ({result['kind']}): {result['error']}. Do this step another way.", file=sys.stderr)
    return 3


def _cmd_cap(args: argparse.Namespace) -> int:
    session_id = _session_id(args)
    if not session_id:
        print("no session id: pass --session or run this from a Claude Code session", file=sys.stderr)
        return 2
    if args.tool:
        external.save_caps(session_id, {args.tool: args.limit or "off"})
    print(json.dumps(external.load_caps(session_id)))
    return 0


def _cmd_inventory(args: argparse.Namespace) -> int:
    print(json.dumps(inventory.load(max_age=0 if args.refresh else inventory.REFRESH_SECONDS), indent=2))
    return 0


def _cmd_update(args: argparse.Namespace) -> int:
    try:
        data = update.refresh(paths.data_file("models.json") if args.repo else None)
    except Exception as error:  # network or parse failure
        if not args.quiet:
            print(f"catalog not updated: {error}", file=sys.stderr)
        return 1
    if not args.quiet:
        print("models:", ", ".join(m["id"] for m in data["claude"]))
    return 0


def _cmd_exhausted(args: argparse.Namespace) -> int:
    if args.clear:
        inventory.clear_exhausted(args.alias)
    else:
        inventory.mark_exhausted(args.alias, args.hours)
    print(json.dumps(inventory.load().get("exhausted", {})))
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    results = doctor.run()
    print(doctor.render(results))
    return 1 if any(status == doctor.FAIL for _, status, _ in results) else 0


def _cmd_stats(args: argparse.Namespace) -> int:
    data = stats.summarize(stats.transcripts(args.days))
    print(json.dumps(data, indent=2) if args.json else stats.render(data, args.days))
    return 0


ENVIRONMENT = [
    ("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "optional: the host's compaction window (100000 to 1000000). Unset, the model's own window applies"),
    ("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", "optional: compact at this percent of the window; read by the compaction guard"),
    ("ANTHROPIC_MODEL", "chat model, read for the ceiling"),
    ("CLAUDE_CODE_EFFORT_LEVEL", "chat effort, read for the ceiling"),
    ("CLAUDE_CODE_SUBAGENT_MODEL", "if set, it overrides the model of every worker; unset it so routing can choose"),
    ("CLAUDE_CODE_SESSION_ID", "set by Claude Code; `token-beggar note`, `ask` and `cap` use it"),
    ("TOKEN_BEGGAR", "off disables the hooks for this process"),
    ("TOKEN_BEGGAR_HOME", "state directory"),
    ("TOKEN_BEGGAR_MODE", "off, lean or full: force how much the skill acts, instead of reading the measured ratio for the ceiling"),
    ("TOKEN_BEGGAR_EARLY", "1 turns on the early /compact suggestion at a finished phase (off by default, not measured to save)"),
    ("TOKEN_BEGGAR_OFFLINE", "1 never fetches the models page and never lists external models"),
    ("TOKEN_BEGGAR_EXTERNAL", "comma list of the external AIs routing may use, for example agy; none turns them all off"),
    ("TOKEN_BEGGAR_EXTERNAL_TIMEOUT", "seconds an external AI call may run (default 600)"),
    ("TOKEN_BEGGAR_SETTLE", "seconds the footer waits for the last message to reach the transcript (default 4)"),
]


def _cmd_env(args: argparse.Namespace) -> int:
    for name, meaning in ENVIRONMENT:
        print(f"{name:<34}{meaning}")
    print(f"\nstate directory: {paths.home()}")
    return 0


def _cmd_window(args: argparse.Namespace) -> int:
    top = ceiling.resolve(None, None)
    point = compact.resolve(None, catalog.find(args.model or top["model"]))
    print(json.dumps(point, indent=2) if args.json else _window_text(point))
    return 0


def _window_text(point: dict) -> str:
    state = "OFF (auto compaction is disabled)" if point["disabled"] else "on"
    if point["user_set"]:
        mine = "set by you, so Token Beggar does not move it"
    else:
        mine = (
            "the host default; Token Beggar defers a mid-step compaction (never past "
            f"{point['defer_limit']:,}). The early /compact suggestion is off unless TOKEN_BEGGAR_EARLY=1. "
            "It writes no settings, because the host reads the window only at startup"
        )
    return (
        f"compaction point: {point['threshold']:,} tokens ({point['source']}), auto compaction {state}\n"
        f"window {point['window']:,} of a {point['context_window']:,} context\n"
        f"{mine}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="token-beggar", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    menu = sub.add_parser("menu", help="show every provider, model and effort routing can pick for a ceiling")
    menu.add_argument("--model")
    menu.add_argument("--effort", choices=catalog.EFFORTS)
    menu.add_argument("--session")
    menu.add_argument("--json", action="store_true")
    menu.set_defaults(func=_cmd_menu)
    mode = sub.add_parser("mode", help="show how much the skill acts for a ceiling, from the measured cost ratio")
    mode.add_argument("--model")
    mode.add_argument("--effort", choices=catalog.EFFORTS)
    mode.add_argument("--all", action="store_true", help="every measured model at every effort")
    mode.set_defaults(func=_cmd_mode)

    note = sub.add_parser("note", help="save the note for the next compaction (text as arguments or on stdin)")
    state = note.add_mutually_exclusive_group(required=True)
    state.add_argument("--mid-step", action="store_true", help="work is half done: defer the compaction a little")
    state.add_argument("--clean", action="store_true", help="at a clean stopping point")
    state.add_argument("--phase-done", action="store_true", help="a phase just finished: a good moment to compact early")
    note.add_argument("--progress", type=float, help="how far the current step is, 0 to 1; scales how long a compaction may be deferred")
    note.add_argument("--needs-early-detail", action="store_true", help="later work depends on early details: keep more context")
    note.add_argument("--session")
    note.add_argument("text", nargs="*")
    note.set_defaults(func=_cmd_note)

    ask = sub.add_parser("ask", help="hand one task to an external AI (agy, gemini, codex) and print its answer")
    ask.add_argument("tool", choices=["agy", "gemini", "codex"])
    ask.add_argument("--model")
    ask.add_argument("--file", action="append", default=[], help="a file whose text goes into the prompt (repeatable)")
    ask.add_argument("--session")
    ask.add_argument("task", nargs="+")
    ask.set_defaults(func=_cmd_ask)

    cap = sub.add_parser(
        "cap", help="cap an external AI for this session, e.g. `cap agy flash`; `cap agy` switches it off; no arguments shows the caps"
    )
    cap.add_argument("tool", nargs="?", choices=["agy", "gemini", "codex"])
    cap.add_argument("limit", nargs="?")
    cap.add_argument("--session")
    cap.set_defaults(func=_cmd_cap)

    inv = sub.add_parser("inventory", help="list the models and tools this machine can reach")
    inv.add_argument("--refresh", action="store_true")
    inv.set_defaults(func=_cmd_inventory)

    upd = sub.add_parser("update", help="refresh the model catalog from the public models page")
    upd.add_argument("--quiet", action="store_true")
    upd.add_argument("--repo", action="store_true", help="write data/models.json in this checkout (used by the weekly Action)")
    upd.set_defaults(func=_cmd_update)

    gone = sub.add_parser("exhausted", help="mark a Claude alias as out of quota, so routing skips it")
    gone.add_argument("alias", nargs="?")
    gone.add_argument("--hours", type=float, default=5.0)
    gone.add_argument("--clear", action="store_true")
    gone.set_defaults(func=_cmd_exhausted)

    check = sub.add_parser("doctor", help="check that the hooks run and nothing is silently switching routing off")
    check.set_defaults(func=_cmd_doctor)

    stat = sub.add_parser("stats", help="what the workers did in your recent sessions, from your own transcripts")
    stat.add_argument("--days", type=float, default=7)
    stat.add_argument("--json", action="store_true")
    stat.set_defaults(func=_cmd_stats)

    env = sub.add_parser("env", help="list the environment variables and the state directory this tool uses")
    env.set_defaults(func=_cmd_env)

    window = sub.add_parser("window", help="print the compaction point in use")
    window.add_argument("--model")
    window.add_argument("--json", action="store_true")
    window.set_defaults(func=_cmd_window)

    hook = sub.add_parser("hook", help="entry point used by Claude Code hooks")
    hook.add_argument("event", choices=["prompt", "pretool", "posttool", "stop", "precompact", "sessionstart"])
    hook.set_defaults(func=lambda a: hooks.run(a.event))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

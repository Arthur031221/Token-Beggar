"""Command line: `python3 -m token_beggar <command>`."""

import argparse
import json
import sys

from . import __version__, catalog, ceiling, compact, doctor, hooks, inventory, paths, routes, stats, update


def _cmd_route(args: argparse.Namespace) -> int:
    top = ceiling.resolve(None, None)
    if args.model:
        top = {**top, "model": catalog.find(args.model).id, "known": True}
    if args.effort:
        top["effort"] = args.effort
    rows = routes.table(top, inventory.exhausted_aliases(inventory.load()))
    print(json.dumps({"ceiling": top, "routes": rows}, indent=2) if args.json else _render(top, rows))
    return 0


def _render(top: dict, rows: list[dict]) -> str:
    out = [f"ceiling: {top['model'] or 'unknown'} at {top['effort']}"]
    for row in rows:
        out.append(f"{row['class']:<14} {row['model']:<7} {row['effort']:<7} {row['mode']}")
    return "\n".join(out)


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
    ("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "the host's compaction point; the guard needs it (60000 or more)"),
    ("ANTHROPIC_MODEL", "chat model, read for the ceiling"),
    ("CLAUDE_CODE_EFFORT_LEVEL", "chat effort, read for the ceiling"),
    ("CLAUDE_CODE_SUBAGENT_MODEL", "if set, it overrides the model of every worker; unset it so routing can choose"),
    ("TOKEN_BEGGAR", "off disables the hooks for this process"),
    ("TOKEN_BEGGAR_HOME", "state directory"),
    ("TOKEN_BEGGAR_OFFLINE", "1 never fetches the models page"),
]


def _cmd_env(args: argparse.Namespace) -> int:
    for name, meaning in ENVIRONMENT:
        print(f"{name:<34}{meaning}")
    print(f"\nstate directory: {paths.home()}")
    return 0


def _cmd_window(args: argparse.Namespace) -> int:
    print(compact.configured_window() or "not set: the guard only writes handoff notes")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="token-beggar", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    route = sub.add_parser("route", help="show the routing table for a ceiling")
    route.add_argument("--model")
    route.add_argument("--effort", choices=catalog.EFFORTS)
    route.add_argument("--json", action="store_true")
    route.set_defaults(func=_cmd_route)

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
    window.set_defaults(func=_cmd_window)

    hook = sub.add_parser("hook", help="entry point used by Claude Code hooks")
    hook.add_argument("event", choices=["prompt", "precompact", "sessionstart"])
    hook.set_defaults(func=lambda a: hooks.run(a.event))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

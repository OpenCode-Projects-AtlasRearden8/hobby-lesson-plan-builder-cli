"""Command line entry point.

Run with:
    python -m lesson_builder topics.txt --sessions 4

Drafting help from a local Ollama (or any OpenAI-compatible endpoint) is
strictly opt-in via --draft; without that flag nothing touches the network.
"""

import argparse
import sys
from typing import List, Optional

from . import cards, pacing
from . import __version__
from .drafting import DEFAULT_API_BASE, DEFAULT_MODEL, draft_session_notes
from .model import parse_bullet_list


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lesson-builder",
        description=(
            "Turn a bullet list of what a beginner should learn into a "
            "friendly, printable lesson plan with graded pacing, "
            "one-page lesson cards, supply lists, and checkboxes."
        ),
        epilog=(
            "Drafting help is off by default and never required. "
            "With --draft it talks to a local OpenAI-compatible endpoint "
            "(Ollama) at --api-base; no API key is used unless you pass one."
        ),
    )
    parser.add_argument("bullet_file", help="text file with one bullet per line ('-' reads stdin)")
    parser.add_argument("--title", default="Your Learning Plan", help="plan title")
    parser.add_argument(
        "--sessions", type=int, default=0,
        help="number of sessions (0 = auto-suggest from --minutes)",
    )
    parser.add_argument(
        "--minutes", type=int, default=pacing.DEFAULT_MINUTES_PER_SESSION,
        help="minutes to spend per session for auto-pacing (default 45)",
    )
    parser.add_argument(
        "--max-topics", type=int, default=pacing.DEFAULT_MAX_TOPICS_PER_SESSION,
        help="at most this many topics per session (default 6)",
    )
    parser.add_argument(
        "--supplies", default="", metavar="ITEMS",
        help="extra comma-separated supplies to add to every session",
    )
    parser.add_argument("--format", default="text", choices=["text", "markdown"],
                        help="output format (default text)")
    parser.add_argument("--output", metavar="FILE", help="write plan to FILE instead of stdout")
    parser.add_argument("--draft", action="store_true",
                        help="optional: ask a model for friendly first-step blurbs "
                             "(uses --api-base; off by default)")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE,
                        help="OpenAI-compatible chat completions base URL "
                             "(default: local Ollama)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="model name (default llama3.2)")
    parser.add_argument("--api-key", default=None,
                        help="optional bearer key for hosted endpoints; "
                             "none is needed for local Ollama")
    parser.add_argument("--version", action="version", version=f"lesson-builder {__version__}")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    raw = ""
    if args.bullet_file == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(args.bullet_file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"lesson-builder: cannot read {args.bullet_file!r}: {exc}", file=sys.stderr)
            return 2
    items = parse_bullet_list(raw)
    if not items:
        print(
            "lesson-builder: no topics found. Paste a bullet list, one item per line:\n"
            "  - what a prompt is\n"
            "  - writing my first prompt",
            file=sys.stderr,
        )
        return 2

    extra_supplies = [s.strip() for s in args.supplies.split(",") if s.strip()]
    plan = pacing.build_plan(
        items,
        title=args.title,
        session_count=args.sessions,
        minutes_per_session=args.minutes,
        max_topics=args.max_topics,
        extra_supplies=extra_supplies,
    )

    optional_note = ""
    if args.draft:
        hint = (
            f"drafting topics for "
            f"{args.model} at {args.api_base} — offline plan is below "
            "either way"
        )
        for session in plan.sessions:
            session.notes = draft_session_notes(
                [t.text for t in session.topics],
                session.number,
                api_base=args.api_base,
                model=args.model,
                api_key=args.api_key,
            )
        optional_note = (
            f"(Drafting attempted: {hint}.)\n"
            if plan.sessions
            else ""
        )

    rendered = cards.render_plan(plan, fmt=args.format)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(rendered)
        except OSError as exc:
            print(f"lesson-builder: cannot write {args.output!r}: {exc}", file=sys.stderr)
            return 2
        sessions_line = ", ".join(str(s.number) for s in plan.sessions)
        print(
            f"{optional_note}Wrote {plan.topic_count} topics across sessions "
            f"{sessions_line} to {args.output}"
        )
    else:
        if optional_note:
            print(optional_note, file=sys.stderr)
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Printable one-page lesson cards and markdown plans.

Cards are drawn as simple text boxes with progress checkboxes, sized to
fit one printed page when the plan is a few sessions. Rendering is
deterministic and offline.
"""

from typing import List, Optional, Sequence

from .model import LessonPlan, Session

CARD_WIDTH = 74  # leaves margins on a printed page


def _wrap(text: str, width: int) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    line = words[0]
    for word in words[1:]:
        if len(line) + 1 + len(word) <= width:
            line = f"{line} {word}"
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def _box_line(left: str = "", center: str = "", right: str = "") -> str:
    """One interior row of a card, padded to CARD_WIDTH."""
    inner = CARD_WIDTH - 4  # |️ + one space each side
    if center:
        text = _truncate(center, inner)
        pad = (inner - len(text)) // 2
        body = " " * pad + text
        return f"| {body.ljust(inner)} |"
    left = _truncate(left, inner)
    if right:
        right = _truncate(right, max(0, inner - len(left) - 1))
        body = left.ljust(inner - len(right) - 1) + " " + right
    else:
        body = left.ljust(inner)
    return f"| {body} |"


def _border() -> str:
    inner = CARD_WIDTH - 2
    top = f"|{'-' * inner}|"
    return top


def _blank() -> str:
    return _box_line()


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


def _labeled_block(label: str, lines: Sequence[str]) -> List[str]:
    out = [_blank(), _box_line(label.upper())]
    for line in lines:
        for wrapped in _wrap(line.strip(), CARD_WIDTH - 6):
            out.append(_box_line(f"  {wrapped}"))
    return out


def render_card(session: Session, plan: LessonPlan, width: Optional[int] = None) -> List[str]:
    """One card as a list of lines, each no wider than CARD_WIDTH."""
    assert width in (None, CARD_WIDTH), "card width is fixed for printing"
    lines: List[str] = []
    minutes = session.minutes
    lines.append(_border())
    lines.append(
        _box_line(
            left=f"Session {session.number} of {len(plan.sessions)}",
            right=f"~{minutes} min",
        )
    )
    lines.append(_box_line(center=plan.title))
    lines.append(_box_line(left="Goal: learn a little bit, enjoy it, come back next time."))

    # Checklist
    lines.append(_blank())
    lines.append(_box_line("CHECKLIST — tick one box each time:"))
    for topic in session.topics:
        wrapped = _wrap(topic.text, CARD_WIDTH - 11)
        lines.append(_box_line(f"  [ ] {wrapped[0]}"))
        for extra in wrapped[1:]:
            lines.append(_box_line(f"      {extra}"))

    # Supplies
    lines.extend(_labeled_block("Supplies to have ready", session.supplies.items))

    # Optional drafted notes (only present when the user opted into --draft)
    if session.notes.strip():
        note_lines: List[str] = []
        for raw in session.notes.splitlines():
            note_lines.extend(_wrap(raw.strip(), CARD_WIDTH - 6))
        lines.extend(_labeled_block("Notes from your drafting helper", note_lines))

    # Gentle framing
    lines.append(_blank())
    lines.append(_box_line("BEFORE YOU START"))
    lines.append(_box_line("  Take a slow breath. Two minutes of anything counts."))
    lines.append(_box_line("  If you get stuck, stop and come back tomorrow. That is normal."))
    lines.append(_border())
    return lines


def render_card_text(session: Session, plan: LessonPlan) -> str:
    return "\n".join(render_card(session, plan)) + "\n"


def render_plan_text(plan: LessonPlan) -> str:
    """All cards stacked with page gaps, ready to print."""
    parts: List[str] = []
    for i, session in enumerate(plan.sessions):
        if i:
            parts.append("\n" + "-" * CARD_WIDTH + "\n")
        parts.append(render_card_text(session, plan))
    return "".join(parts)


def render_plan_markdown(plan: LessonPlan) -> str:
    out: List[str] = [f"# {plan.title}", ""]
    for session in plan.sessions:
        out.append(f"## Session {session.number} (~{session.minutes} minutes)")
        out.append("")
        out.append("**Checklist**")
        for topic in session.topics:
            out.append(f"- [ ] {topic.text}")
        out.append("")
        out.append("**Supplies to have ready**")
        for item in session.supplies.items:
            out.append(f"- {item}")
        out.append("")
    return "\n".join(out) + "\n"


def render_plan(plan: LessonPlan, fmt: str = "text") -> str:
    if fmt == "text":
        return render_plan_text(plan)
    if fmt == "markdown":
        return render_plan_markdown(plan)
    raise ValueError(f"unknown format: {fmt!r} (use 'text' or 'markdown')")

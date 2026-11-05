"""Core data model for lesson plans."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Topic:
    """A single skill or idea the learner should pick up."""

    text: str
    tier: int = 1  # 0 = friendly starter, 1 = everyday idea, 2 = bigger stretch

    @property
    def minutes(self) -> int:
        """Rough time budget for this topic (used for pacing only)."""
        return {0: 20, 1: 30, 2: 45}[self.tier]


@dataclass
class Supplies:
    """Things to have on hand for a session."""

    items: List[str] = field(default_factory=list)


@dataclass
class Session:
    """One lesson gathering: its topics, supplies, and checklist."""

    number: int
    topics: List[Topic] = field(default_factory=list)
    supplies: Supplies = field(default_factory=Supplies)
    notes: str = ""

    @property
    def minutes(self) -> int:
        return sum(t.minutes for t in self.topics)


@dataclass
class LessonPlan:
    """A whole course plan, ready to print."""

    title: str
    sessions: List[Session] = field(default_factory=list)

    @property
    def topic_count(self) -> int:
        return sum(len(s.topics) for s in self.sessions)


def parse_bullet_list(text: str) -> List[str]:
    """Pull bullet items out of a pasted list.

    Accepts markdown bullets ("- item", "* item", "+ item"), number lists
    ("1. item"), and plain lines. Blank lines and a leading markdown
    heading (#...) are ignored.
    """
    items: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line[:2] in ("- ", "* ", "+ "):
            item = line[2:]
        elif line[:3] == "1. ":
            item = line[3:]
        else:
            # Numbered bullets like "12. item" or "3) item"
            i = 0
            while i < len(line) and line[i].isdigit():
                i += 1
            if i and i + 1 < len(line) and line[i] in ".)" and line[i + 1] == " ":
                item = line[i + 2 :]
            else:
                item = line
        item = item.strip()
        if item:
            items.append(item)
    return items

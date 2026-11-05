"""Graded pacing across sessions.

The pacing math here is fully deterministic and offline: no network, no
model calls. Drafting help (optional, off by default) only adds friendly
blurb text on top of whatever pacing computes.
"""

from typing import List, Sequence, Tuple

from .model import LessonPlan, Session, Topic, Supplies

# Words that hint a topic is a friendly starting point...
STARTER_HINTS = (
    "what is", "what are", "why", "basics", "basic", "introduction",
    "intro", "getting started", "start", "beginner", "first", "fundamentals",
    "simple", "easy", "overview", "tour", "hello",
)
# ...and words that hint a topic is a bigger stretch.
STRETCH_HINTS = (
    "advanced", "automat", "api", "deploy", "optimi", "integrat",
    "script", "troubleshoot", "architecture", "architect", "debug",
    "security", "privacy", "policy", "custom", "workflow", "pipeline",
    "build", "create", "project", "practice",
)

DEFAULT_MINUTES_PER_SESSION = 45
DEFAULT_MAX_TOPICS_PER_SESSION = 6


def grade_topic(text: str) -> int:
    """Score a topic into tiers: 0 starter, 1 everyday, 2 stretch.

    Stretch hints win over starter hints, because a bullet like
    "basics of the API" is still mostly an API topic.
    """
    low = text.lower()
    if any(h in low for h in STRETCH_HINTS):
        return 2
    if any(h in low for h in STARTER_HINTS):
        return 0
    return 1


def sort_graded(topics: Sequence[Topic]) -> List[Topic]:
    """Stable-sort topics so gentle ones come before stretchy ones.

    Stability keeps the learner's original order inside each tier,
    which respects the intent of their bullet list.
    """
    return sorted(topics, key=lambda t: t.tier)


def distribute_sessions(
    topics: Sequence[Topic],
    session_count: int,
    max_topics: int = DEFAULT_MAX_TOPICS_PER_SESSION,
) -> List[List[Topic]]:
    """Split graded topics across sessions, gentle topics first.

    Sessions are filled in order to a near-equal minute budget, so
    early sessions lean friendly and later ones carry the stretch.
    Guarantees (when sessions <= len(topics)):
      * every topic assigned exactly once, and
      * no session is empty, and
      * per-session topic caps are honored as far as the topic count allows.
    """
    if session_count < 1:
        raise ValueError("session_count must be at least 1")
    if not topics:
        return [[] for _ in range(session_count)]
    session_count = min(session_count, len(topics))
    ordered = sort_graded(topics)
    total = sum(t.minutes for t in ordered)
    target = total / session_count
    groups: List[List[Topic]] = []
    idx = 0
    for s in range(session_count):
        remaining_sessions = session_count - s
        remaining_sessions_topics = len(ordered) - idx
        cap = max_topics if max_topics >= 1 else DEFAULT_MAX_TOPICS_PER_SESSION
        cap = min(cap, remaining_sessions_topics - (remaining_sessions - 1))
        load = 0
        group: List[Topic] = []
        while idx < len(ordered):
            if group and (
                len(group) >= cap
                or (load + ordered[idx].minutes) > target
            ):
                break
            group.append(ordered[idx])
            load += ordered[idx].minutes
            idx += 1
        groups.append(group)
    # If topic caps squeezed some topics out, tuck the leftovers (the
    # stretchiest ones) into the latest sessions so nothing is lost.
    while idx < len(ordered):
        for s in range(session_count - 1, -1, -1):
            if idx >= len(ordered):
                break
            groups[s].append(ordered[idx])
            idx += 1
    return groups


def suggest_session_count(
    topics: Sequence[Topic],
    minutes_per_session: int = DEFAULT_MINUTES_PER_SESSION,
) -> int:
    """How many sessions this list needs, at a friendly pace per meeting."""
    if minutes_per_session < 1:
        raise ValueError("minutes_per_session must be at least 1")
    if not topics:
        return 0
    total = sum(t.minutes for t in topics)
    return max(1, -(-total // minutes_per_session))  # ceil division


def build_supplies(session: Session, extra: Sequence[str] = ()) -> List[str]:
    """A short supply list for one session.

    The friendly defaults stay the same every session; keyword hints add
    anything specific the topics imply. Extra items are appended, but
    duplicates are skipped.
    """
    items = ["Notebook and pen", "Something to drink or snack on"]
    low = " ".join(t.text.lower() for t in session.topics)
    if any(w in low for w in ("computer", "laptop", "install", "software",
                              "online", "app", "web", "code", "account",
                              "email", "ai")):
        items.insert(1, "Computer or laptop with internet")
    if any(w in low for w in ("print", "card", "poster", "flyer", "sheet")):
        items.insert(1, "Printer or printed handouts")
    seen = set()
    result: List[str] = []
    for item in list(items) + [e for e in extra if e.strip()]:
        key = item.strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


def build_plan(
    bullet_items: Sequence[str],
    title: str = "Your Learning Plan",
    session_count: int = 0,
    minutes_per_session: int = DEFAULT_MINUTES_PER_SESSION,
    max_topics: int = DEFAULT_MAX_TOPICS_PER_SESSION,
    extra_supplies: Sequence[str] = (),
) -> LessonPlan:
    """Turn a bullet list into a paced LessonPlan (offline, deterministic).

    With session_count of 0, sessions are auto-suggested from the
    minutes per session.
    """
    topics = [Topic(text=item, tier=grade_topic(item)) for item in bullet_items]
    if session_count <= 0:
        session_count = suggest_session_count(topics, minutes_per_session)
        session_count = min(
            session_count, len(topics) or 1
        )  # don't create empties for a tiny list

    groups = distribute_sessions(topics, session_count, max_topics)
    plan = LessonPlan(title=title)
    for number, group in enumerate(groups, start=1):
        session = Session(number=number, topics=group)
        session.supplies = Supplies(
            items=build_supplies(session, extra_supplies)
        )
        plan.sessions.append(session)
    return plan


def pacing_summary(plan: LessonPlan) -> Tuple[int, int]:
    """(total topics, total minutes) for a plan; handy for tests and headers."""
    return plan.topic_count, sum(s.minutes for s in plan.sessions)

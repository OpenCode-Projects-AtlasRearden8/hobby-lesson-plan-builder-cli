import unittest

from lesson_builder.model import Topic, parse_bullet_list
from lesson_builder.pacing import (
    DEFAULT_MAX_TOPICS_PER_SESSION,
    build_plan,
    build_supplies,
    distribute_sessions,
    grade_topic,
    sort_graded,
    suggest_session_count,
)


def ts(*texts):
    return [Topic(text=t, tier=grade_topic(t)) for t in texts]


class GradeTopicTests(unittest.TestCase):
    def test_starter_intro_is_tier_0(self):
        self.assertEqual(grade_topic("what is a prompt"), 0)
        self.assertEqual(grade_topic("getting started with chat"), 0)

    def test_stretch_api_is_tier_2(self):
        self.assertEqual(grade_topic("Automation with an API workflow"), 2)

    def test_plain_topic_is_tier_1(self):
        self.assertEqual(grade_topic("reading the reply"), 1)

    def test_first_word_not_alone_enough(self):
        self.assertEqual(grade_topic("writing my very own prompt style"), 1)

    def test_case_insensitive(self):
        self.assertEqual(grade_topic("WHAT IS AI"), 0)
        self.assertEqual(grade_topic("DEPLOYING ADVANCED PIPELINES"), 2)

    def test_stretch_wins_over_starter(self):
        # "basics of the API" is mostly an API topic.
        self.assertEqual(grade_topic("basics of the API"), 2)


class SortGradgedTests(unittest.TestCase):
    def test_stable_within_tier(self):
        topics = ts("weird thing", "what is ai", "build a workflow", "cool thing", "why learn ai")
        graded = sort_graded(topics)
        tiers = [t.tier for t in graded]
        self.assertEqual(tiers, sorted(tiers))
        self.assertEqual(graded[0].text, "what is ai")
        self.assertEqual(graded[-1].text, "build a workflow")
        self.assertEqual(graded[3].text, "cool thing")  # same-topic order kept


class SuggestSessionCountTests(unittest.TestCase):
    def test_single_light_topic_is_one_session(self):
        self.assertEqual(suggest_session_count(ts("what is a prompt")), 1)

    def test_divides_with_ceiling(self):
        # two starter topics * 20 min = 40 min => 1 session at 45 min
        self.assertEqual(suggest_session_count(ts("what is ai", "why learn ai"), 45), 1)
        # three starters (60) + one stretch (45) = 105 => 3 sessions at 45 min
        self.assertEqual(
            suggest_session_count(
                ts("what is ai", "why learn ai", "what is a prompt", "why practice prompts"), 45
            ),
            3,
        )

    def test_zero_minutes_rejected(self):
        with self.assertRaises(ValueError):
            suggest_session_count(ts("anything"), 0)

    def test_empty_list_is_zero_sessions(self):
        self.assertEqual(suggest_session_count([]), 0)


class DistributeSessionsTests(unittest.TestCase):
    def test_every_topic_assigned_exactly_once(self):
        groups = distribute_sessions(ts("what is ai", "prompt basics", "writing first prompts", "api", "deploy workflow", "advanced pipeline"), 3)
        self.assertEqual(sum(len(g) for g in groups), 6)
        items = [t.text for g in groups for t in g]
        self.assertEqual(len(set(items)), 6)

    def test_no_empty_sessions(self):
        topics = ts("what is ai", "what is a prompt", "prompt patterns", "custom api")
        groups = distribute_sessions(topics, 4)
        self.assertEqual(len(groups), 4)
        self.assertTrue(all(groups))  # topics > sessions, so none may be empty

    def test_sessions_capped_at_topic_count(self):
        # More requested sessions than topics is capped to the topic count.
        groups = distribute_sessions(ts("what is ai"), 5)
        self.assertEqual([len(g) for g in groups], [1])

    def test_graded_order_starters_first(self):
        topics = ts("advanced pipeline", "what is ai", "custom api workflow", "why learn ai")
        groups = distribute_sessions(topics, 2)
        first, second = groups[0], groups[1]
        self.assertTrue(all(t.tier <= max(t2.tier for t2 in second) for t in first))
        self.assertLessEqual(max(t.tier for t in first), max(t.tier for t in second))
        self.assertEqual(sum(t.tier for t in first) / len(first), 0.0)  # all starters
        self.assertGreater(max(t.tier for t in second), 0)

    def test_max_topics_cap_respected_when_capacity_allows(self):
        topics = ts(*[f"topic {i}" for i in range(6)])
        groups = distribute_sessions(topics, session_count=3, max_topics=2)
        self.assertEqual([len(g) for g in groups], [2, 2, 2])

    def test_overflow_topics_are_kept_not_dropped(self):
        # Caps cannot hold 10 topics in 2 sessions of 3; nothing may vanish.
        topics = ts(*[f"topic {i}" for i in range(10)])
        groups = distribute_sessions(topics, session_count=2, max_topics=3)
        self.assertEqual(sum(len(g) for g in groups), 10)
        self.assertTrue(all(groups))

    def test_loads_near_balanced(self):
        topics = ts("what is ai", "what is a prompt", "reading a reply", "prompt patterns", "custom api workflow", "deploy pipeline", "advanced automation")
        groups = distribute_sessions(topics, 3)
        loads = [sum(t.minutes for t in g) for g in groups]
        # slack of at most one heavy topic between any two sessions
        self.assertLessEqual(max(loads) - min(loads), 45)
        self.assertLessEqual(max(len(g) for g in groups), DEFAULT_MAX_TOPICS_PER_SESSION)

    def test_error_on_zero_sessions(self):
        with self.assertRaises(ValueError):
            distribute_sessions(ts("anything"), 0)

    def test_empty_topics_returns_empty_groups(self):
        self.assertEqual(distribute_sessions([], 3), [[], [], []])


class BuildPlanTests(unittest.TestCase):
    def test_auto_sessions_fill_from_pacing(self):
        plan = build_plan(["what is ai", "why learn ai", "prompt basics", "writing first prompts", "reading a reply", "custom api workflow", "deploy pipeline", "advanced automation"], minutes_per_session=45)
        self.assertEqual(plan.topic_count, 8)
        self.assertTrue(all(s.topics for s in plan.sessions))
        minutes = [s.minutes for s in plan.sessions]
        self.assertTrue(all(m <= 45 + 45 for m in minutes))  # one session never exceeds target + a full topic

    def test_fixed_sessions_respected(self):
        plan = build_plan(["what is ai", "prompt basics", "advanced pipeline"], session_count=2)
        self.assertEqual(len(plan.sessions), 2)

    def test_extra_supplies_deduped_and_present(self):
        plan = build_plan(["what is a prompt"], extra_supplies=("chocolate", " computer or laptop"))
        supplies = plan.sessions[0].supplies.items
        self.assertIn("chocolate", supplies)
        self.assertEqual(supplies.count("computer or laptop"), 1)

    def test_supply_hint_computer(self):
        plan = build_plan(["installing software on a computer"])
        self.assertIn("Computer or laptop with internet", plan.sessions[0].supplies.items)

    def test_supply_hint_printer(self):
        plan = build_plan(["printing a card"])
        self.assertIn("Printer or printed handouts", plan.sessions[0].supplies.items)

    def test_default_supplies_always_there(self):
        plan = build_plan(["anything"])
        supplies = plan.sessions[0].supplies.items
        self.assertIn("Notebook and pen", supplies)
        self.assertIn("Something to drink or snack on", supplies)

    def test_empty_spaces_skipped(self):
        from lesson_builder.model import Session

        session = Session(number=1, topics=ts("anything"))
        supplies = build_supplies(session, extra=["", " ", "tea"])
        self.assertEqual(supplies.count("tea"), 1)
        self.assertNotIn("", supplies)


class ParseBulletListTests(unittest.TestCase):
    def test_markdown_bullets(self):
        self.assertEqual(parse_bullet_list("- a\n* b\n+ c"), ["a", "b", "c"])

    def test_numbered_bullets(self):
        self.assertEqual(parse_bullet_list("1. yes\n12. maybe\n2) no"), ["yes", "maybe", "no"])

    def test_plain_lines_and_blank_and_heading(self):
        text = "# welcome\n\njust a sentence\n\n- bullet one"
        self.assertEqual(parse_bullet_list(text), ["just a sentence", "bullet one"])

    def test_empty(self):
        self.assertEqual(parse_bullet_list(""), [])


if __name__ == "__main__":
    unittest.main()

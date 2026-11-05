import unittest

from lesson_builder import cards
from lesson_builder.pacing import build_plan


def plan_for(*topics, sessions=2, extra_supplies=()):
    return build_plan(
        list(topics),
        title="Learning AI, kindly",
        session_count=sessions,
        extra_supplies=extra_supplies,
    )


class CardWidthTests(unittest.TestCase):
    def setUp(self):
        self.plan = plan_for(
            "what is ai",
            "why learn ai",
            "what is a prompt",
            "prompt basics",
            "custom api workflow",
            "advanced automation pipeline",
        )

    def test_no_line_exceeds_card_width(self):
        for session in self.plan.sessions:
            for line in cards.render_card(session, self.plan):
                self.assertLessEqual(len(line), cards.CARD_WIDTH, f"too wide: {line!r}")

    def test_borders_line_up(self):
        for session in self.plan.sessions:
            rendered = cards.render_card(session, self.plan)
            self.assertTrue(all(line.startswith("|") and line.endswith("|") for line in rendered))
            self.assertTrue(len({line for line in rendered if line == cards._border()}) == 1)

    def test_long_topic_text_is_wrapped_not_truncated_mid_word(self):
        text = cards.render_plan_text(self.plan)
        self.assertIn("advanced", text)  # wrapped topic text survives
        for line in text.splitlines():
            self.assertLessEqual(len(line), cards.CARD_WIDTH, f"too wide: {line!r}")

    def test_long_supply_line_does_not_break_border(self):
        plan = build_plan(["what is a prompt"], extra_supplies=("A very long supply item, " * 6 + "end",))
        for session in plan.sessions:
            for line in cards.render_card(session, plan):
                self.assertLessEqual(len(line), cards.CARD_WIDTH)


class CardContentTests(unittest.TestCase):
    def setUp(self):
        self.plan = plan_for(
            "what is a prompt",
            "writing first prompts",
            extra_supplies=("Tea",),
        )
        self.session = self.plan.sessions[0]

    def test_topic_checkboxes_present_per_topic(self):
        text = cards.render_card_text(self.session, self.plan)
        self.assertEqual(text.count("[ ]"), len(self.session.topics))

    def test_supplies_section_present(self):
        text = cards.render_card_text(self.session, self.plan)
        self.assertIn("SUPPLIES", text.upper())
        self.assertIn("Notebook and pen", text)
        self.assertIn("Tea", text)

    def test_session_header_shows_number_and_minutes(self):
        text = cards.render_card_text(self.session, self.plan)
        self.assertIn(f"Session {self.session.number} of {len(self.plan.sessions)}", text)
        self.assertIn(f"~{self.session.minutes} min", text)

    def test_plan_title_centered_on_card(self):
        text = cards.render_card_text(self.session, self.plan)
        title_line = next(line for line in text.splitlines() if "Learning AI, kindly" in line)
        stripped = title_line.rstrip("|").rstrip()
        left_pad = len(stripped) - len(stripped.lstrip())
        right_pad = len(str(title_line)) - len(str(title_line).rstrip()) - left_pad
        self.assertLess(abs(left_pad - right_pad), 2)

    def test_render_card_text_ends_with_newline(self):
        self.assertTrue(cards.render_card_text(self.session, self.plan).endswith("\n"))

    def test_checklist_count_matches_markdown(self):
        md = cards.render_plan_markdown(self.plan)
        self.assertEqual(md.count("- [ ]"), self.plan.topic_count)


class MarkdownPlanTests(unittest.TestCase):
    def test_headers_and_checkboxes(self):
        plan = plan_for("what is a prompt", "build a workflow", sessions=1)
        md = cards.render_plan_markdown(plan)
        self.assertTrue(md.startswith("# Learning AI, kindly"))
        self.assertIn("## Session 1 (~", md)
        self.assertEqual(md.count("- [ ]"), 2)

    def test_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            cards.render_plan(build_plan(["anything"]), fmt="html")


class NotesSectionTests(unittest.TestCase):
    def test_no_notes_section_by_default(self):
        plan = plan_for("what is a prompt")
        text = cards.render_card_text(plan.sessions[0], plan)
        self.assertNotIn("Notes from your drafting helper", text)

    def test_notes_rendered_when_present(self):
        plan = plan_for("what is a prompt")
        plan.sessions[0].notes = "First things first:\n  - Open the chat and say hi."
        text = cards.render_card_text(plan.sessions[0], plan)
        self.assertIn("NOTES FROM YOUR DRAFTING HELPER", text)
        self.assertIn("Open the chat and say hi.", text)

    def test_blanks_notes_skipped(self):
        plan = plan_for("what is a prompt")
        plan.sessions[0].notes = "   "
        text = cards.render_card_text(plan.sessions[0], plan)
        self.assertNotIn("Notes from your drafting helper", text)


class FullPlanTextTests(unittest.TestCase):
    def test_two_sessions_separated(self):
        plan = plan_for("what is ai", "prompt basics", "advanced pipeline", sessions=2)
        text = cards.render_plan_text(plan)
        self.assertIn("Session 1 of 2", text)
        self.assertIn("Session 2 of 2", text)
        self.assertEqual(text.count(cards._border()), 4)  # top+bottom per card


if __name__ == "__main__":
    unittest.main()

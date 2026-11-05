import json
import unittest
import urllib.error
from unittest import mock

from lesson_builder import drafting


class BuildPromptTests(unittest.TestCase):
    def test_mentions_session_and_topics_in_order(self):
        prompt = drafting.build_prompt(["learn a", "learn b"], 3)
        self.assertIn("Session 3 topics:", prompt)
        self.assertIn("- learn a", prompt)
        self.assertIn("- learn b", prompt)
        self.assertIn("same order", prompt)


class RequestBlurbTests(unittest.TestCase):
    def _fake_response(self, content):
        payload = {"choices": [{"message": {"content": content}}]}
        return mock.mock_open(read_data=json.dumps(payload).encode("utf-8")).return_value

    def test_parses_one_blurb_per_topic(self):
        opener = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "Open it.\nType something."}}]}
        ).encode("utf-8")
        ctx.__enter__.return_value = ctx
        opener.return_value = ctx
        with mock.patch("urllib.request.urlopen", opener):
            blurbs = drafting.request_blurbs(["a", "b"], 1, api_base="http://x/v1")
        self.assertEqual(blurbs, ["Open it.", "Type something."])

    def test_sent_to_chat_completions_with_model(self):
        opener = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.read.return_value = b'{"choices":[{"message":{"content":"hi"}}]}'
        ctx.__enter__.return_value = ctx
        opener.return_value = ctx
        with mock.patch("urllib.request.urlopen", opener):
            drafting.request_blurbs(["a"], 1)
        data = json.loads(opener.call_args[0][0].data.decode("utf-8"))
        self.assertEqual(data["model"], drafting.DEFAULT_MODEL)
        self.assertFalse(data["stream"])
        self.assertIn("/chat/completions", opener.call_args[0][0].full_url)

    def test_no_auth_header_without_key(self):
        opener = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.read.return_value = b'{"choices":[{"message":{"content":"hi"}}]}'
        ctx.__enter__.return_value = ctx
        opener.return_value = ctx
        with mock.patch("urllib.request.urlopen", opener):
            drafting.request_blurbs(["a"], 1)
        request = opener.call_args[0][0]
        self.assertNotIn("Authorization", request.headers)

    def test_auth_header_only_when_key_given(self):
        opener = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.read.return_value = b'{"choices":[{"message":{"content":"hi"}}]}'
        ctx.__enter__.return_value = ctx
        opener.return_value = ctx
        with mock.patch("urllib.request.urlopen", opener):
            drafting.request_blurbs(["a"], 1, api_key="secret")
        request = opener.call_args[0][0]
        self.assertEqual(request.headers.get("Authorization"), "Bearer secret")

    def test_connection_error_when_server_down(self):
        with mock.patch(
            "urllib.request.urlopen",
            mock.MagicMock(side_effect=urllib.error.URLError("refused")),
        ):
            with self.assertRaises(ConnectionError):
                drafting.request_blurbs(["a"], 1)

    def test_timeout_maps_to_connection_error(self):
        with mock.patch(
            "urllib.request.urlopen",
            mock.MagicMock(side_effect=TimeoutError("slow")),
        ):
            with self.assertRaises(ConnectionError):
                drafting.request_blurbs(["a"], 1)

    def test_bad_payload_returns_empty(self):
        opener = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.read.return_value = b'{"oops": true}'
        ctx.__enter__.return_value = ctx
        opener.return_value = ctx
        with mock.patch("urllib.request.urlopen", opener):
            self.assertEqual(drafting.request_blurbs(["a"], 1), [])

    def test_empty_items_short_circuits(self):
        self.assertEqual(drafting.request_blurbs([], 1), [])


class DraftingOffByDefaultTests(unittest.TestCase):
    def test_real_network_is_untouched_without_opt_in(self):
        # The CLI only calls draft_session_notes when --draft is passed;
        # guard here that the default endpoint is a local one.
        self.assertTrue(
            drafting.DEFAULT_API_BASE.startswith("http://localhost"),
            "default endpoint must be local-first",
        )


class FallbackTests(unittest.TestCase):
    def test_fallback_message_when_offline(self):
        with mock.patch(
            "lesson_builder.drafting.request_blurbs",
            mock.MagicMock(side_effect=ConnectionError("no server")),
        ):
            note = drafting.draft_session_notes(["a"], 1, api_base="http://localhost:1/v1")
        self.assertIn("Drafting unavailable", note)
        self.assertIn("no server", note)

    def test_successful_drafts_formatted(self):
        with mock.patch(
            "lesson_builder.drafting.request_blurbs",
            mock.MagicMock(return_value=["Open the chat.", "Type hi."]),
        ):
            note = drafting.draft_session_notes(["a", "b"], 1)
        self.assertIn("First things first:", note)
        self.assertIn("- Open the chat.", note)
        self.assertIn("- Type hi.", note)


if __name__ == "__main__":
    unittest.main()

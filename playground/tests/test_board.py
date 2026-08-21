import unittest

from playground.board import BoardContext

A = {"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0}
B = {
    "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
    "edges": [{"from": "a", "to": "c", "label": "GET"}],
    "unreadable": 0,
}


class TestBoardContext(unittest.TestCase):
    def test_starts_with_no_messages(self):
        self.assertEqual(BoardContext().messages(), [])

    def test_one_update_yields_one_message(self):
        b = BoardContext()
        b.update(A)
        self.assertEqual(len(b.messages()), 1)

    def test_many_updates_still_yield_one_message(self):
        """A ten-minute session must not accumulate two hundred copies of a
        diagram. The board message is replaced in place, never appended."""
        b = BoardContext()
        for _ in range(200):
            b.update(B)
        self.assertEqual(len(b.messages()), 1)

    def test_the_message_names_the_components(self):
        b = BoardContext()
        b.update(B)
        text = b.messages()[0]["content"]
        self.assertIn("App", text)
        self.assertIn("Cache", text)
        self.assertIn("GET", text)

    def test_it_reports_what_just_changed(self):
        b = BoardContext()
        b.update(A)
        b.update(B)
        self.assertIn("Cache", b.last_change_summary)

    def test_unreadable_strokes_are_declared_not_guessed(self):
        b = BoardContext()
        b.update({"nodes": [], "edges": [], "unreadable": 3})
        self.assertIn("3", b.messages()[0]["content"])

    # --- gaps not covered above ---

    def test_no_change_summary_on_the_first_update(self):
        """On the first update there is no previous graph to diff against --
        everything on the board is new, so nothing has "just" changed."""
        b = BoardContext()
        b.update(A)
        self.assertEqual(b.last_change_summary, "")

    def test_unreadable_count_is_the_exact_number_not_a_substring_match(self):
        """Guards against a render that merely contains the digit "3"
        somewhere unrelated (e.g. 3 nodes) instead of actually reporting the
        unreadable-stroke count. Uses a count that shares no digits with the
        node/edge counts it sits next to."""
        b = BoardContext()
        b.update({"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 7})
        text = b.messages()[0]["content"]
        self.assertIn("7 freehand marks", text)

    def test_no_unreadable_line_when_there_is_nothing_unreadable(self):
        b = BoardContext()
        b.update(A)
        self.assertNotIn("freehand", b.messages()[0]["content"])

    def test_an_isolated_component_is_named_even_without_an_edge(self):
        """In graph B every node also appears in the Connections line, so a
        renderer that dropped the Components line entirely would still pass
        test_the_message_names_the_components. An isolated, edge-less node
        catches that: it can only show up via the Components line."""
        b = BoardContext()
        b.update(
            {
                "nodes": [{"id": "a", "label": "App"}, {"id": "q", "label": "Queue"}],
                "edges": [],
                "unreadable": 0,
            }
        )
        self.assertIn("Queue", b.messages()[0]["content"])

    def test_second_update_replaces_the_rendered_content_not_just_the_count(self):
        """The single message's content must reflect the latest graph, not
        the first one -- proves replacement, not just single-message count."""
        b = BoardContext()
        b.update(A)
        b.update(B)
        text = b.messages()[0]["content"]
        self.assertIn("Cache", text)
        self.assertIn("GET", text)


if __name__ == "__main__":
    unittest.main()

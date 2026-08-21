import unittest

from playground.board import BoardContext

A = {"nodes": [{"id": "a", "label": "App"}], "edges": [], "unreadable": 0}
B = {
    "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
    "edges": [{"from": "a", "to": "c", "label": "GET"}],
    "unreadable": 0,
}

# A cache-aside diagram (App reads through Cache and DB) and the same board
# with Cache -- and both its edges -- erased.
CACHE_ASIDE = {
    "nodes": [
        {"id": "a", "label": "App"},
        {"id": "c", "label": "Cache"},
        {"id": "d", "label": "DB"},
    ],
    "edges": [
        {"from": "a", "to": "c", "label": "GET"},
        {"from": "a", "to": "d", "label": "GET"},
    ],
    "unreadable": 0,
}
CACHE_REMOVED = {
    "nodes": [{"id": "a", "label": "App"}, {"id": "d", "label": "DB"}],
    "edges": [{"from": "a", "to": "d", "label": "GET"}],
    "unreadable": 0,
}
# Same nodes as B, but the edge between them is erased -- an edge removal
# with no node removal, to isolate that case from CACHE_REMOVED's node loss.
EDGE_REMOVED = {
    "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
    "edges": [],
    "unreadable": 0,
}
# From CACHE_ASIDE: Cache is removed *and* a Queue is added in the same step.
MIXED_ADD_AND_REMOVE = {
    "nodes": [
        {"id": "a", "label": "App"},
        {"id": "d", "label": "DB"},
        {"id": "q", "label": "Queue"},
    ],
    "edges": [{"from": "a", "to": "d", "label": "GET"}],
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

    # --- removals: the summary must not be deaf to deletions ---

    def test_a_removed_component_is_reported(self):
        """Deleting Cache from a cache-aside diagram must not be silent --
        it's either a correction or a mistake, and a coach should react."""
        b = BoardContext()
        b.update(CACHE_ASIDE)
        b.update(CACHE_REMOVED)
        summary = b.last_change_summary
        self.assertIn("removed", summary)
        self.assertIn("Cache", summary)

    def test_a_removed_connection_is_reported_without_a_node_removal(self):
        """Erasing just the edge between two nodes that both still exist is
        a distinct case from a node disappearing -- isolate it."""
        b = BoardContext()
        b.update(B)
        b.update(EDGE_REMOVED)
        summary = b.last_change_summary
        self.assertIn("disconnected", summary)
        self.assertIn("App", summary)
        self.assertIn("Cache", summary)
        self.assertNotIn("removed", summary)

    def test_a_mixed_update_reports_both_the_addition_and_the_removal(self):
        b = BoardContext()
        b.update(CACHE_ASIDE)
        b.update(MIXED_ADD_AND_REMOVE)
        summary = b.last_change_summary
        self.assertIn("added", summary)
        self.assertIn("Queue", summary)
        self.assertIn("removed", summary)
        self.assertIn("Cache", summary)

    # --- malformed boards must degrade, not crash a live session ---

    def test_missing_unreadable_key_does_not_crash(self):
        b = BoardContext()
        b.update({"nodes": [], "edges": []})
        self.assertEqual(len(b.messages()), 1)

    def test_completely_empty_graph_does_not_crash(self):
        b = BoardContext()
        b.update({})
        self.assertEqual(len(b.messages()), 1)
        self.assertIn("none yet", b.messages()[0]["content"])

    def test_a_node_without_a_label_does_not_crash(self):
        b = BoardContext()
        b.update({"nodes": [{"id": "x"}], "edges": [], "unreadable": 0})
        text = b.messages()[0]["content"]
        self.assertIn("(unlabelled)", text)

    def test_an_edge_without_a_label_does_not_crash(self):
        b = BoardContext()
        b.update(
            {
                "nodes": [{"id": "a", "label": "App"}, {"id": "c", "label": "Cache"}],
                "edges": [{"from": "a", "to": "c"}],
                "unreadable": 0,
            }
        )
        text = b.messages()[0]["content"]
        self.assertIn("App -> Cache", text)

    def test_a_node_missing_its_id_is_skipped_not_fatal(self):
        b = BoardContext()
        b.update({"nodes": [{"label": "Ghost"}, {"id": "a", "label": "App"}], "edges": [], "unreadable": 0})
        text = b.messages()[0]["content"]
        self.assertIn("App", text)
        self.assertNotIn("Ghost", text)

    def test_an_edge_missing_an_endpoint_is_skipped_not_fatal(self):
        b = BoardContext()
        b.update(
            {
                "nodes": [{"id": "a", "label": "App"}],
                "edges": [{"from": "a", "label": "GET"}],
                "unreadable": 0,
            }
        )
        self.assertEqual(len(b.messages()), 1)
        self.assertNotIn("Connections", b.messages()[0]["content"])

    # --- unlabelled wording must match between the render and the summary ---

    def test_unlabelled_node_wording_matches_in_render_and_summary(self):
        b = BoardContext()
        b.update({"nodes": [{"id": "a"}], "edges": [], "unreadable": 0})
        b.update({"nodes": [{"id": "a"}, {"id": "q"}], "edges": [], "unreadable": 0})
        rendered = b.messages()[0]["content"]
        summary = b.last_change_summary
        self.assertIn("(unlabelled)", rendered)
        self.assertIn("(unlabelled)", summary)

    # --- a label can be any JSON shape over the wire; it must stringify, not crash ---

    def test_an_int_label_renders_as_a_string_not_a_crash(self):
        b = BoardContext()
        b.update({"nodes": [{"id": "a", "label": 123}], "edges": [], "unreadable": 0})
        self.assertIn("123", b.messages()[0]["content"])

    def test_a_list_label_renders_as_a_string_not_a_crash(self):
        b = BoardContext()
        b.update({"nodes": [{"id": "a", "label": ["x", "y"]}], "edges": [], "unreadable": 0})
        self.assertIn("x", b.messages()[0]["content"])

    def test_a_dict_label_renders_as_a_string_not_a_crash(self):
        b = BoardContext()
        b.update({"nodes": [{"id": "a", "label": {"weird": True}}], "edges": [], "unreadable": 0})
        self.assertIn("weird", b.messages()[0]["content"])

    def test_a_non_string_label_appears_in_the_change_summary_too(self):
        """The rendered text and the change summary share _name -- a
        non-string label must not crash either path, and both must agree."""
        b = BoardContext()
        b.update(A)
        b.update(
            {
                "nodes": [{"id": "a", "label": "App"}, {"id": "q", "label": 456}],
                "edges": [],
                "unreadable": 0,
            }
        )
        self.assertIn("456", b.last_change_summary)


if __name__ == "__main__":
    unittest.main()

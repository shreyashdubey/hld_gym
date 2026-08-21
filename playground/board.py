"""The board's presence in the LLM context: one message, replaced in place.

Appending each update would put two hundred copies of a diagram in a ten-minute
session's context and bill for every one of them.
"""


class BoardContext:
    def __init__(self) -> None:
        self._graph: dict | None = None
        self._previous: dict | None = None

    def update(self, graph: dict) -> None:
        self._previous, self._graph = self._graph, graph

    def messages(self) -> list[dict]:
        if self._graph is None:
            return []
        return [{"role": "system", "content": self._render(self._graph)}]

    @property
    def last_change_summary(self) -> str:
        """One line naming what appeared since the previous update. Empty on the
        first update, when everything is new and nothing has 'just' changed."""
        if self._previous is None or self._graph is None:
            return ""
        before = {n["id"] for n in self._previous["nodes"]}
        added = [n["label"] or n["id"] for n in self._graph["nodes"] if n["id"] not in before]
        before_edges = {(e["from"], e["to"]) for e in self._previous["edges"]}
        new_edges = [e for e in self._graph["edges"] if (e["from"], e["to"]) not in before_edges]
        parts = []
        if added:
            parts.append("added " + ", ".join(added))
        if new_edges:
            names = {n["id"]: (n["label"] or n["id"]) for n in self._graph["nodes"]}
            parts.append(
                "connected "
                + ", ".join(f"{names.get(e['from'], '?')}->{names.get(e['to'], '?')}" for e in new_edges)
            )
        return "; ".join(parts)

    @staticmethod
    def _render(graph: dict) -> str:
        names = {n["id"]: (n["label"] or "(unlabelled)") for n in graph["nodes"]}
        lines = ["The candidate's whiteboard right now:"]
        lines.append("Components: " + (", ".join(names.values()) or "none yet"))
        if graph["edges"]:
            lines.append(
                "Connections: "
                + ", ".join(
                    f"{names.get(e['from'], '?')} -> {names.get(e['to'], '?')}"
                    + (f" ({e['label']})" if e["label"] else "")
                    for e in graph["edges"]
                )
            )
        if graph["unreadable"]:
            lines.append(
                f"There are {graph['unreadable']} freehand marks you cannot read. "
                "Ask what they are rather than guessing."
            )
        return "\n".join(lines)

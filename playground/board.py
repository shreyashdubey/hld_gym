"""The board's presence in the LLM context: one message, replaced in place.

Appending each update would put two hundred copies of a diagram in a ten-minute
session's context and bill for every one of them.
"""

UNLABELLED = "(unlabelled)"


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
        """One line naming what appeared or disappeared since the previous
        update. Empty on the first update, when everything is new and
        nothing has 'just' changed."""
        if self._previous is None or self._graph is None:
            return ""
        before_nodes, before_edges = self._nodes(self._previous), self._edges(self._previous)
        after_nodes, after_edges = self._nodes(self._graph), self._edges(self._graph)

        before_ids = {n["id"] for n in before_nodes}
        after_ids = {n["id"] for n in after_nodes}
        names_before = {n["id"]: self._name(n) for n in before_nodes}
        names_after = {n["id"]: self._name(n) for n in after_nodes}

        added = [names_after[n["id"]] for n in after_nodes if n["id"] not in before_ids]
        removed = [names_before[n["id"]] for n in before_nodes if n["id"] not in after_ids]

        before_edge_keys = {(e["from"], e["to"]) for e in before_edges}
        after_edge_keys = {(e["from"], e["to"]) for e in after_edges}
        new_edges = [e for e in after_edges if (e["from"], e["to"]) not in before_edge_keys]
        gone_edges = [e for e in before_edges if (e["from"], e["to"]) not in after_edge_keys]

        parts = []
        if added:
            parts.append("added " + ", ".join(added))
        if removed:
            parts.append("removed " + ", ".join(removed))
        if new_edges:
            parts.append(
                "connected "
                + ", ".join(
                    f"{names_after.get(e['from'], '?')} to {names_after.get(e['to'], '?')}"
                    for e in new_edges
                )
            )
        if gone_edges:
            parts.append(
                "disconnected "
                + ", ".join(
                    f"{names_before.get(e['from'], '?')} to {names_before.get(e['to'], '?')}"
                    for e in gone_edges
                )
            )
        return "; ".join(parts)

    @staticmethod
    def _name(node: dict) -> str:
        """The label, coerced to a string. A board arrives as untyped JSON
        from a browser; a label can be any shape. Falsy or missing reads as
        unlabelled -- everything else is stringified, never fatal."""
        label = node.get("label")
        return str(label) if label else UNLABELLED

    @staticmethod
    def _usable_id(value: object) -> bool:
        """An id both this class and a dict/set can hold. JSON's only
        unhashable shapes are list and object, and both arrive here: a
        browser sending {"id": {...}} used to reach `{n["id"] for n in ...}`
        and raise TypeError: unhashable type. That raised *after* update()
        had already swapped the graph in, so every later render and every
        later push_context() in the session raised too -- including the
        session cap's coach handover, the one thing the cap exists to
        guarantee. Dropped here, in the one place both _render and
        last_change_summary read through, rather than guarded at each use."""
        return not isinstance(value, (list, dict))

    @classmethod
    def _nodes(cls, graph: dict) -> list[dict]:
        """Nodes that can actually be referenced: dicts carrying a usable id.
        Anything else is dropped rather than crashing a live session."""
        return [
            n
            for n in (graph.get("nodes") or [])
            if isinstance(n, dict) and "id" in n and cls._usable_id(n["id"])
        ]

    @classmethod
    def _edges(cls, graph: dict) -> list[dict]:
        """Edges that can actually be drawn: dicts carrying both endpoints."""
        return [
            e
            for e in (graph.get("edges") or [])
            if isinstance(e, dict)
            and "from" in e
            and "to" in e
            and cls._usable_id(e["from"])
            and cls._usable_id(e["to"])
        ]

    @classmethod
    def _render(cls, graph: dict) -> str:
        nodes, edges = cls._nodes(graph), cls._edges(graph)
        names = {n["id"]: cls._name(n) for n in nodes}
        lines = ["The candidate's whiteboard right now:"]
        lines.append("Components: " + (", ".join(names.values()) or "none yet"))
        if edges:
            lines.append(
                "Connections: "
                + ", ".join(
                    f"{names.get(e['from'], '?')} -> {names.get(e['to'], '?')}"
                    + (f" ({e['label']})" if e.get("label") else "")
                    for e in edges
                )
            )
        unreadable = graph.get("unreadable") or 0
        if unreadable:
            lines.append(
                f"There are {unreadable} freehand marks you cannot read. "
                "Ask what they are rather than guessing."
            )
        return "\n".join(lines)

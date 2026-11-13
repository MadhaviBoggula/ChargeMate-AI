"""Owner graph (Member 4 framework + Member 2 domain workflow).

Placeholder until Member 2 delivers owner domain nodes; composes the shared
building blocks only.
"""
from app.agents.shared.runtime import register_graph


def build_owner_graph():
    from app.agents.shared.runtime import build_default_graph

    return build_default_graph()


register_graph("owner", build_owner_graph)

"""Driver graph (Member 4 framework + Member 3 domain workflow).

Placeholder until Member 3 delivers driver/booking nodes; composes the shared
building blocks only. Booking confirmation pause/resume plugs into
``GraphState.pending_confirmation`` here.
"""
from app.agents.shared.runtime import register_graph


def build_driver_graph():
    from app.agents.shared.runtime import build_default_graph

    return build_default_graph()


register_graph("driver", build_driver_graph)

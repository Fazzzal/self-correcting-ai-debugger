from app.graph.state import DebugState


def route_after_evaluate(state: DebugState) -> str:
    """
    Decides where the graph goes after evaluation.
    Returns one of: "success", "retry", "give_up"
    """
    if state["success"]:
        return "success"
    if state["attempt"] >= state["max_attempts"]:
        return "give_up"
    return "retry"
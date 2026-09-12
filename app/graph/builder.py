from langgraph.graph import StateGraph, END

from app.graph.state import DebugState
from app.graph.nodes import analyze_node, generate_fix_node, execute_node, evaluate_node
from app.graph.edges import route_after_evaluate


def build_graph():
    graph = StateGraph(DebugState)

    graph.add_node("analyze", analyze_node)
    graph.add_node("generate_fix", generate_fix_node)
    graph.add_node("execute", execute_node)
    graph.add_node("evaluate", evaluate_node)

    graph.set_entry_point("analyze")

    graph.add_edge("analyze", "generate_fix")
    graph.add_edge("generate_fix", "execute")
    graph.add_edge("execute", "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "success": END,
            "give_up": END,
            "retry": "generate_fix",
        },
    )

    return graph.compile()
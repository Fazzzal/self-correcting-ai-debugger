from app.graph.state import DebugState
from app.llm.gemini_client import get_llm
from app.llm.prompts import build_analysis_prompt, build_fix_prompt, extract_code, normalize_llm_content
from app.sandbox.executor import run_sandboxed


def analyze_node(state: DebugState) -> DebugState:
    """
    Diagnoses the current code + latest error using the LLM.
    Does not modify the code — only produces an analysis.
    """
    llm = get_llm()
    prompt = build_analysis_prompt(state["current_code"], state.get("execution_error"))
    result = llm.invoke(prompt)
    state["analysis"] = normalize_llm_content(result.content)
    return state


def generate_fix_node(state: DebugState) -> DebugState:
    """
    Produces a corrected version of the code based on the analysis
    and the full error history (to avoid repeating past mistakes).
    """
    llm = get_llm()
    prompt = build_fix_prompt(
        state["current_code"],
        state["analysis"],
        state["error_history"],
    )
    result = llm.invoke(prompt)
    state["current_code"] = extract_code(result.content)
    state["attempt"] += 1
    return state


def execute_node(state: DebugState) -> DebugState:
    """
    Runs the current code in the sandbox and records the outcome.
    """

    stdout, stderr = run_sandboxed(state["current_code"])
    state["execution_output"] = stdout
    state["execution_error"] = stderr

    if stderr:
        state["error_history"].append(stderr)

    return state


def evaluate_node(state: DebugState) -> DebugState:
    """
    Marks success/failure based on the last execution.
    Routing (retry vs give up) happens separately in edges.py — this node
    only records the outcome.
    """
    state["success"] = state["execution_error"] is None

    if state["success"]:
        state["final_status"] = "success"
    elif state["attempt"] >= state["max_attempts"]:
        state["final_status"] = "gave_up"
    # else: leave final_status as None — the graph will loop back
    return state
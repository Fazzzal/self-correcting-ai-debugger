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
    Marks success/failure. If the user supplied expected_output, success
    requires an exact match (after trimming whitespace) in addition to
    clean execution. Otherwise, success just means no execution error —
    and we flag that this was NOT a verified-correct result.
    """
    ran_cleanly = state["execution_error"] is None
    expected = state.get("expected_output")

    if expected is not None and expected.strip() != "":
        actual = (state["execution_output"] or "").strip()
        matches_expected = actual == expected.strip()
        state["success"] = ran_cleanly and matches_expected
        state["correctness_checked"] = True

        if ran_cleanly and not matches_expected:
            # Treat a wrong-output result as a new "error" so the retry loop
            # has something concrete to react to
            mismatch_msg = (
                f"Output mismatch. Expected:\n{expected.strip()}\n"
                f"Got:\n{actual}"
            )
            state["execution_error"] = mismatch_msg
            state["error_history"].append(mismatch_msg)
    else:
        state["success"] = ran_cleanly
        state["correctness_checked"] = False

    if state["success"]:
        state["final_status"] = "success"
    elif state["attempt"] >= state["max_attempts"]:
        state["final_status"] = "gave_up"

    return state
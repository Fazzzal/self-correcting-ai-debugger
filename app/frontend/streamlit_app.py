import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from app.graph.builder import build_graph

st.set_page_config(page_title="Self-Correcting AI Code Debugger", layout="wide")
st.title("Self-Correcting AI Code Debugger")
st.caption("Paste buggy Python code below. The system will analyze, fix, execute, and retry automatically.")

with st.sidebar:
    st.header("Settings")
    max_attempts = st.number_input("Max debug attempts", min_value=1, max_value=10, value=5)

code_input = st.text_area(
    "Buggy Python code",
    height=300,
    placeholder="def add(a, b)\n    return a + b",
)

run_button = st.button("Debug this code", type="primary")

# Maps internal node names to friendly labels for the live log
NODE_LABELS = {
    "analyze": "Analyzing the bug",
    "generate_fix": "Generating a fix",
    "execute": "Running the code in the sandbox",
    "evaluate": "Evaluating the result",
}

if run_button:
    if not code_input.strip():
        st.warning("Please paste some code first.")
    else:
        graph = build_graph()

        initial_state = {
            "original_code": code_input,
            "current_code": code_input,
            "error_history": [],
            "analysis": None,
            "execution_output": None,
            "execution_error": None,
            "success": False,
            "attempt": 0,
            "max_attempts": max_attempts,
            "final_status": None,
        }

        live_log = st.container()
        final_result = None

        with live_log:
            st.subheader("Live debugging log")

            for step in graph.stream(initial_state, stream_mode="updates"):
                for node_name, node_state in step.items():
                    label = NODE_LABELS.get(node_name, node_name)
                    attempt_num = node_state.get("attempt", initial_state["attempt"])

                    with st.status(f"Attempt {attempt_num}: {label}", state="running", expanded=False) as status:
                        if node_name == "analyze":
                            st.write(node_state.get("analysis", ""))
                            status.update(label=f"Attempt {attempt_num}: Analysis complete", state="complete")

                        elif node_name == "generate_fix":
                            st.code(node_state.get("current_code", ""), language="python")
                            status.update(label=f"Attempt {attempt_num}: Fix generated", state="complete")

                        elif node_name == "execute":
                            err = node_state.get("execution_error")
                            out = node_state.get("execution_output")
                            if err:
                                st.error(err)
                                status.update(label=f"Attempt {attempt_num}: Execution failed", state="error")
                            else:
                                st.code(out or "(no output)")
                                status.update(label=f"Attempt {attempt_num}: Execution succeeded", state="complete")

                        elif node_name == "evaluate":
                            status.update(
                                label=f"Attempt {attempt_num}: Success={node_state.get('success')}",
                                state="complete",
                            )
                            final_result = node_state

        st.divider()
        if final_result:
            if final_result.get("final_status") == "success":
                st.success(f"Fixed successfully in {final_result['attempt']} attempt(s).")
            else:
                st.error(f"Gave up after {final_result['attempt']} attempt(s). Manual review needed.")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original code")
                st.code(code_input, language="python")
            with col2:
                st.subheader("Final code")
                st.code(final_result.get("current_code", ""), language="python")
# Self-Correcting AI Code Debugger

An agentic Python debugger that uses Google's Gemini API, LangChain, and
LangGraph to automatically diagnose, fix, and verify Python code — retrying
with feedback from each failed attempt until the code runs successfully or
a maximum retry limit is reached.

## How it works

1. **Analyze** — Gemini diagnoses the bug type and root cause.
2. **Generate fix** — Gemini proposes a corrected version, informed by the
   full history of prior errors in this session.
3. **Execute** — the code runs in an isolated sandbox (subprocess, no
   network access, static AST checks against dangerous imports/calls,
   hard timeout).
4. **Evaluate** — if execution succeeded, done. If not, and attempts remain,
   loop back to step 2 with the new error added to history.



Get a free Gemini API key at https://aistudio.google.com/apikey



## Known limitations

- Evaluation only checks whether execution *completed without error* —
  it does not verify output *correctness* against expected behavior.
  A logically wrong-but-non-crashing fix will be marked "success."
- The sandbox blocks common dangerous imports/calls via a static AST
  check plus subprocess isolation, but this is not a hardened security
  boundary — for untrusted, large-scale, or production use, this should
  be replaced with containerized (Docker) execution.
- Gemini free-tier rate limits (RPM/RPD) apply; heavy retry loops on
  larger `max_attempts` can hit these limits.

## Tech stack

Python · LangChain · LangGraph · Google Gemini API · Streamlit
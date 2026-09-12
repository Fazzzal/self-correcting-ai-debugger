"""
Sandboxed execution of LLM-generated Python code.

Two layers of protection:
1. Static AST check — rejects code that imports dangerous modules or calls
   dangerous builtins, before anything runs.
2. Subprocess isolation — runs the code in a separate process with a
   stripped environment and a hard timeout.

This is NOT a full security sandbox (it doesn't stop CPU/memory abuse from
non-banned stdlib code, and a sufficiently creative payload could still find
gaps). For a hobby/project-scale debugger this is a reasonable baseline.
If you ever run untrusted code at scale, move this into a locked-down
Docker container instead.
"""

import ast
import os
import subprocess
import sys
import tempfile

BANNED_NAMES = {"os", "subprocess", "sys", "shutil", "socket", "requests", "urllib"}
BANNED_CALLS = {"eval", "exec", "__import__", "open", "compile"}


def static_safety_check(code: str) -> str | None:
    """
    Walks the AST looking for banned imports or calls.
    Returns a human-readable violation message, or None if the code looks safe.
    If the code has a syntax error, we skip this check and let real execution
    surface the SyntaxError properly (that's a legitimate bug to fix, not a
    security concern).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level = alias.name.split(".")[0]
                if top_level in BANNED_NAMES:
                    return f"Import of '{top_level}' is not allowed in the sandbox"

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_level = node.module.split(".")[0]
                if top_level in BANNED_NAMES:
                    return f"Import of '{top_level}' is not allowed in the sandbox"

        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BANNED_CALLS:
                return f"Call to '{func.id}' is not allowed in the sandbox"

    return None


def run_sandboxed(code: str, timeout: int = 10) -> tuple[str | None, str | None]:
    """
    Runs `code` in an isolated subprocess.

    Returns:
        (stdout, stderr) — stderr is None if execution succeeded cleanly.
        If the sandbox rejects the code outright, stdout is None and stderr
        contains the rejection reason.
    """
    violation = static_safety_check(code)
    if violation:
        return None, f"Sandbox rejected code: {violation}"

    path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            path = f.name

        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PATH": os.environ.get("PATH", "")},
        )

        if result.returncode != 0:
            return result.stdout, result.stderr.strip()
        return result.stdout, None

    except subprocess.TimeoutExpired:
        return None, f"Execution timed out after {timeout} seconds"

    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


if __name__ == "__main__":
    # quick manual smoke test
    print(run_sandboxed("print('hello world')"))
    print(run_sandboxed("print(1/0)"))
    print(run_sandboxed("import os\nos.system('echo hi')"))
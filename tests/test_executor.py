from app.sandbox.executor import run_sandboxed, static_safety_check


def test_clean_execution():
    out, err = run_sandboxed("print('hello')")
    assert err is None
    assert "hello" in out


def test_runtime_error_captured():
    out, err = run_sandboxed("print(1/0)")
    assert err is not None
    assert "ZeroDivisionError" in err


def test_static_check_blocks_os_import():
    out, err = run_sandboxed("import os\nos.system('echo hi')")
    assert err is not None
    assert "Sandbox rejected" in err


def test_static_check_blocks_eval():
    out, err = run_sandboxed("eval('1+1')")
    assert err is not None
    assert "Sandbox rejected" in err
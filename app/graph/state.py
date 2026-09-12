from typing import TypedDict, Optional

class DebugState(TypedDict):
    original_code: str          # the user's original buggy submission, never overwritten
    current_code: str           # the latest version being tested
    error_history: list[str]    # every error seen so far, oldest to newest
    analysis: Optional[str]     # LLM's diagnosis of the current error
    execution_output: Optional[str]   # stdout from the last run
    execution_error: Optional[str]    # stderr / exception from the last run, None if clean
    success: bool                # whether the current code ran without error
    attempt: int                 # how many fix attempts have been made so far
    max_attempts: int            # configurable ceiling on retries
    final_status: Optional[str]  # "success" | "gave_up", set at the end
    expected_output: Optional[str]  # NEW — user-supplied expected stdout, if any
    correctness_checked: bool  # NEW — whether we actually verified output, or just checked "no crash"
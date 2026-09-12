from app.graph.builder import build_graph

graph = build_graph()

buggy_code = """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers) + 1):
        total += numbers[i]
    return total / len(numbers)

result = calculate_average([10, 20, 30])
print(result)
"""

initial_state = {
    "original_code": buggy_code,
    "current_code": buggy_code,
    "error_history": [],
    "analysis": None,
    "execution_output": None,
    "execution_error": None,
    "success": False,
    "attempt": 0,
    "max_attempts": 5,
    "final_status": None,
}

result = graph.invoke(initial_state)

print("Final status:", result["final_status"])
print("Attempts used:", result["attempt"])
print("Final code:\n", result["current_code"])
print("Output:", result["execution_output"])
print("\n--- Error history ---")
for i, err in enumerate(result["error_history"], start=1):
    print(f"Attempt {i}: {err}")
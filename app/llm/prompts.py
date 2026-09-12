import re
def build_analysis_prompt(code: str, error: str | None) -> str:
    error_section = f"\nThe code produced this error when run:\n{error}" if error else \
        "\nNo execution has happened yet — analyze the code purely by reading it."

    return f"""You are a Python debugging expert. Analyze the following code.
{error_section}

Code:
```python
{code}
```

Identify:
1. The type of bug (syntax, logical, or runtime)
2. The root cause, precisely
3. Which line(s) are responsible

Do NOT fix the code yet. Only diagnose. Be concise — a few sentences, not a report."""


def build_fix_prompt(code: str, analysis: str, error_history: list[str]) -> str:
    history_section = ""
    if error_history:
        joined = "\n---\n".join(error_history)
        history_section = f"\nPrevious errors already seen in this session (avoid reintroducing these):\n{joined}\n"

    return f"""You are a Python debugging expert. Fix the following code based on this analysis.

Analysis:
{analysis}
{history_section}
Code to fix:
```python
{code}
```

Return ONLY the corrected, complete, runnable Python code.
Do not include explanations, markdown formatting, or commentary — just the raw code."""

def normalize_llm_content(content) -> str:
    """
    LangChain's Gemini wrapper sometimes returns .content as a string,
    and sometimes as a list of content blocks (e.g. [{'type': 'text', 'text': '...'}]).
    This flattens either shape into a plain string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)

    return str(content)

def extract_code(llm_output) -> str:
    text = normalize_llm_content(llm_output)
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
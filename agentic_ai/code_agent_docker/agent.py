import requests
import subprocess
import tempfile
import re
import os
import textwrap

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL =  "deepseek-v3.2:cloud"#"llama3.1:8b"


SANDBOX = "/sandbox"
MAX_STEPS = 12


# -------------------------------------------------
# Ollama
# -------------------------------------------------
def call_ollama(prompt: str) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["response"]


# -------------------------------------------------
# Code extraction
# -------------------------------------------------
def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


# -------------------------------------------------
# Execute code
# -------------------------------------------------
def execute(code: str) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", dir=SANDBOX, delete=False
    ) as f:
        f.write(code)
        path = f.name

    try:
        r = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return str(e)


# -------------------------------------------------
# ERROR CLASSIFICATION (MODEL DECIDES)
# -------------------------------------------------
def classify_error(code: str, output: str) -> str:
    prompt = f"""
You are an autonomous debugger.

CODE:
{code}

OUTPUT:
{output}

Classify the failure as ONE of:
- ENV_ERROR (missing dependency, missing binary, permissions, OS, path)
- CODE_ERROR (logic bug, syntax, incorrect API usage)
- UNKNOWN

Output ONLY the label.
"""
    return call_ollama(prompt).strip()


# -------------------------------------------------
# ENV FIX STRATEGY
# -------------------------------------------------
def fix_environment(task: str, code: str, output: str) -> str:
    prompt = f"""
You are fixing an ENVIRONMENT failure.

Task:
{task}

Broken code:
{code}

Error output:
{output}

Rules:
- Output ONLY Python code
- Use python -m pip if installing
- NEVER assume tools exist
- Verify before using
- Use /sandbox paths only
- Be defensive

Goal:
Adapt environment so task can succeed.
"""
    return extract_code(call_ollama(prompt))


# -------------------------------------------------
# CODE FIX STRATEGY
# -------------------------------------------------
def fix_code(task: str, code: str, output: str) -> str:
    prompt = f"""
You are fixing a CODE LOGIC failure.

Task:
{task}

Broken code:
{code}

Error output:
{output}

Rules:
- Output ONLY corrected Python code
- No explanations
- Keep environment assumptions minimal
- Use python -m <module> style
"""
    return extract_code(call_ollama(prompt))


# -------------------------------------------------
# MAIN AGENT LOOP
# -------------------------------------------------
def run_agent(task: str):
    code = ""

    for step in range(1, MAX_STEPS + 1):
        print(f"\n🧠 STEP {step}")

        # generate code if first run
        if not code:
            prompt = f"""
You are a Python autonomous agent running in a Linux container.

Rules:
- Output ONLY Python code
- No explanations
- No markdown
- Assume NOTHING exists
- Verify before use
- Use /sandbox for files
- Prefer python -m <module>

Task:
{task}
"""
            code = extract_code(call_ollama(prompt))

        print("\n📥 CODE:\n", code)

        output = execute(code)
        print("\n📤 OUTPUT:\n", output)

        # success
        if output and not any(x in output for x in ["Traceback", "Error", "Exception"]):
            print("\n✅ TASK COMPLETED")
            return output

        # classify
        error_type = classify_error(code, output)
        print("\n🧩 ERROR TYPE:", error_type)

        if error_type == "ENV_ERROR":
            code = fix_environment(task, code, output)
        elif error_type == "CODE_ERROR":
            code = fix_code(task, code, output)
        else:
            print("\n❌ UNKNOWN FAILURE — stopping")
            return output

    return "\n❌ FAILED AFTER MAX STEPS"


# -------------------------------------------------
# CLI
# -------------------------------------------------
if __name__ == "__main__":
    print(f"🤖 Autonomous Container Agent ({MODEL})")

    while True:
        try:
            task = input("\nTask (or 'exit'): ")
            if task.lower() in {"exit", "quit"}:
                break

            result = run_agent(task)
            print("\n🎯 FINAL RESULT:\n", result)

        except KeyboardInterrupt:
            print("\n👋 Interrupted")
            break

import requests
import subprocess
import tempfile
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b-instruct"

# ⚠️ Güvenlik: yasaklı ifadeler
FORBIDDEN = [
    "import os",
    "import sys",
    "subprocess",
    "socket",
    "requests",
    "__import__",
]

# -------------------------------------------------
# Ollama çağrısı
# -------------------------------------------------
def call_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()["response"]


# -------------------------------------------------
# Markdown temizleme
# -------------------------------------------------
def extract_python_code(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    if match:
        return match.group(1).strip()
    return text.strip()


# -------------------------------------------------
# Basit güvenlik kontrolü
# -------------------------------------------------
def is_code_safe(code: str) -> bool:
    return not any(bad in code for bad in FORBIDDEN)


# -------------------------------------------------
# Kod çalıştırma (sandbox)
# -------------------------------------------------
def run_code(code: str) -> str:
    if not is_code_safe(code):
        return "❌ Unsafe code detected."

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        dir="/sandbox",
        delete=False
    ) as f:
        f.write(code)
        filename = f.name

    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return str(e)


# -------------------------------------------------
# Self-healing agent loop
# -------------------------------------------------
def run_agent(task: str, max_retries: int = 3):
    prompt = f"""
You are a Python assistant.

Rules:
- Output ONLY valid Python code
- No explanations
- No markdown
- Allowed imports: math, datetime, random
- ALL file operations MUST use /sandbox
- Print the result

Task:
{task}
"""

    for attempt in range(1, max_retries + 1):
        raw = call_ollama(prompt)
        print(f"\n📥 Raw model output (attempt {attempt}):\n{raw}")

        code = extract_python_code(raw)
        print("\n🧹 Sanitized code:\n", code)

        output = run_code(code)
        print("\n📤 Execution output:\n", output)

        # ✅ başarı
        if not any(err in output for err in ["Traceback", "Error", "PermissionError"]):
            return output

        # ❌ hata → modele geri ver
        prompt = f"""
The following Python code failed.

Code:
{code}

Error:
{output}

Fix the code.

Rules:
- Output ONLY corrected Python code
- No explanations
- No markdown
- Use /sandbox for file paths
"""

    return "❌ Failed after multiple attempts."


# -------------------------------------------------
# CLI
# -------------------------------------------------
if __name__ == "__main__":
    print("🐳 Docker Code Agent (Ollama powered)")

    while True:
        try:
            task = input("\nTask (or 'exit'): ")
            if task.lower() in {"exit", "quit"}:
                print("👋 Bye")
                break

            result = run_agent(task)
            print("\n✅ Final result:\n", result)

        except KeyboardInterrupt:
            print("\n👋 Interrupted")
            break

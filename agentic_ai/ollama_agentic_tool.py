import json
import requests
from datetime import datetime
import qrcode

# =====================================================
# TOOLS
# =====================================================


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_txt_file(file_path: str, content: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {file_path}: {content}"


def generate_qr_code(data: str, filename: str, image_path: str | None = None):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"{filename}.png")
    return f"QR code saved as {filename}.png"

# =====================================================
# OLLAMA CALL
# =====================================================

def call_ollama(prompt: str) -> str:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b-instruct",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    r.raise_for_status()
    return r.json()["response"]



# =====================================================
# SYSTEM PROMPT
# =====================================================

def build_system_prompt(tools: dict) -> str:
    tool_desc = []
    for name, t in tools.items():
        tool_desc.append(
            f"{name}: {t['description']} | args: {list(t['args'].keys())}"
        )

    return f"""
You are an AI agent that can use tools.

Available tools:
{chr(10).join(tool_desc)}

IMPORTANT RULES:
- If a tool is required, respond ONLY with JSON
- Do NOT explain anything
- Do NOT add extra text
- JSON format MUST be exactly:

{{
  "tool": "<tool_name>",
  "args": {{ "arg": "value" }}
}}

- If no tool is needed, respond with:

{{
  "tool": null,
  "response": "normal text"
}}

Think step by step, but output ONLY JSON.
"""


# =====================================================
# SAFE JSON PARSER
# =====================================================

def parse_json(text: str) -> dict:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"tool": None, "response": text.strip()}


# =====================================================
# AGENT LOOP (MULTI-STEP)
# =====================================================

import re

import re

def run_agent(user_input: str):
    text = user_input.lower()

    # -------------------------------------------------
    # RULE 1: WRITE CURRENT TIME INTO ANY .TXT FILE
    # -------------------------------------------------
    if "current time" in text and "write" in text:
        match = re.search(r"(\w+\.txt)", text)
        if match:
            filename = match.group(1)
            now = get_current_time()
            write_txt_file(filename, now)
            return f"Current time `{now}` has been written to {filename}"

    # -------------------------------------------------
    # RULE 2: GENERATE QR CODE
    # -------------------------------------------------
    if "qr" in text:
        url_match = re.search(r"(https?://\S+|www\.\S+)", user_input)
        if url_match:
            data = url_match.group(1)
            filename = re.sub(r"\W+", "_", data.replace("https://", "").replace("http://", ""))
            generate_qr_code(data=data, filename=filename)
            return f"QR code for `{data}` has been generated as `{filename}.png`"

    # -------------------------------------------------
    # FALLBACK TO LLM (CHAT / INFO ONLY)
    # -------------------------------------------------
    prompt = f"""
You are an AI assistant.

User request:
{user_input}

Respond normally.
"""
    return call_ollama(prompt)


# =====================================================
# CLI
# =====================================================
if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in {"exit", "quit"}:
            break

        answer = run_agent(user_input)
        print("\nAgent:", answer)

"""
ai.py — talks to the AI through OpenRouter.

Sends the conversation to OpenRouter and parses the JSON command the AI
replies with.
"""

import json
import platform
import os
import shutil

try:
    import requests
except ImportError:
    raise SystemExit("Missing dependency. Run:  pip install requests")

import config


def detect_platform() -> str:
    if "com.termux" in os.environ.get("PREFIX", "") or os.environ.get("TERMUX_VERSION"):
        return "Termux/Android"
    return platform.system() or "Unknown"


def env_summary() -> str:
    return (
        f"Operating system: {detect_platform()} ({platform.platform()})\n"
        f"Python: {platform.python_version()}\n"
        f"Current working directory: {os.getcwd()}"
    )


def call_ai(messages) -> str:
    """Send the conversation to OpenRouter and return the raw reply text."""
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://local.osgpt",
        "X-Title": "OSGPT",
    }
    payload = {
        "model": config.MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    resp = requests.post(config.OPENROUTER_URL, headers=headers, json=payload, timeout=180)
    if resp.status_code == 401:
        raise RuntimeError("Unauthorized (401): check your API key in config.py.")
    if resp.status_code == 402:
        raise RuntimeError("Payment required (402): out of credits on OpenRouter.")
    if resp.status_code == 429:
        raise RuntimeError("Rate limited (429): slow down or try again later.")
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_command(text: str) -> dict:
    """Extract the JSON command from the AI reply, tolerating fences/stray text."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON found in AI reply: {text[:200]}")
    return json.loads(text[start:end + 1])
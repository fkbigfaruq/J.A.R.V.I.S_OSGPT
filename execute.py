"""
execute.py — runs the commands the AI sends.

When the AI replies with e.g. {"action": "make_dir", "args": {"path": "demo"}},
main.py passes the action + args here, the matching function runs locally, and
the text result is returned so it can be fed back to the AI.

All commands are cross-platform (Linux, Windows, macOS, Termux/Android).
"""

import os
import shutil
import subprocess
from pathlib import Path

import memory


def list_dir(path: str = ".") -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: path does not exist: {p}"
    if not p.is_dir():
        return f"ERROR: not a directory: {p}"
    entries = []
    for item in sorted(p.iterdir()):
        kind = "DIR " if item.is_dir() else "FILE"
        try:
            size = item.stat().st_size if item.is_file() else ""
        except OSError:
            size = ""
        entries.append(f"{kind}  {item.name}  {size}")
    listing = "\n".join(entries) if entries else "(empty)"
    return f"Contents of {p.resolve()}:\n{listing}"


def read_file(path: str, max_bytes: int = 20000) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: file does not exist: {p}"
    if not p.is_file():
        return f"ERROR: not a file: {p}"
    try:
        data = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"ERROR reading file: {e}"
    if len(data) > max_bytes:
        data = data[:max_bytes] + f"\n...[truncated, {len(data)} bytes total]"
    return f"--- {p.resolve()} ---\n{data}"


def write_file(path: str, content: str = "") -> str:
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"ERROR writing file: {e}"
    return f"OK: wrote {len(content)} bytes to {p.resolve()}"


def make_dir(path: str) -> str:
    p = Path(path).expanduser()
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"ERROR creating directory: {e}"
    return f"OK: directory ready at {p.resolve()}"


def delete(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: path does not exist: {p}"
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    except Exception as e:
        return f"ERROR deleting: {e}"
    return f"OK: deleted {p}"


def change_dir(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_dir():
        return f"ERROR: not a directory: {p}"
    os.chdir(p)
    return f"OK: current directory is now {os.getcwd()}"


def run_command(command: str, timeout: int = 120) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR running command: {e}"
    combined = ""
    if result.stdout:
        combined += f"STDOUT:\n{result.stdout}\n"
    if result.stderr:
        combined += f"STDERR:\n{result.stderr}\n"
    combined += f"EXIT CODE: {result.returncode}"
    if len(combined) > 20000:
        combined = combined[:20000] + "\n...[output truncated]"
    return combined or "(no output)"


# Map action names (from the AI) to functions.
COMMANDS = {
    "list_dir": lambda a: list_dir(a.get("path", ".")),
    "read_file": lambda a: read_file(a.get("path", "")),
    "write_file": lambda a: write_file(a.get("path", ""), a.get("content", "")),
    "make_dir": lambda a: make_dir(a.get("path", "")),
    "delete": lambda a: delete(a.get("path", "")),
    "change_dir": lambda a: change_dir(a.get("path", "")),
    "run_command": lambda a: run_command(a.get("command", ""), int(a.get("timeout", 120))),
    "remember": lambda a: memory.remember(a.get("note", "")),
}

# Commands that ask for confirmation before running (unless --auto is used).
DANGEROUS = {"run_command", "delete"}


def execute(action: str, args: dict) -> str:
    """Run a single command and return its text result."""
    if action not in COMMANDS:
        return f"ERROR: unknown command '{action}'."
    try:
        return COMMANDS[action](args or {})
    except Exception as e:
        return f"ERROR executing {action}: {e}"
"""
memory.py — persistent memory for OSGPT.

Two kinds of memory, saved next to the code so they survive restarts:

1. CONVERSATION memory  -> memory/history.json
   The full chat (system/user/assistant turns). On startup OSGPT reloads it
   so it remembers what you and your friends were doing before.

2. LONG-TERM memory     -> memory/notes.md
   A plain-text scratchpad of durable facts (your name, preferred stack,
   project locations, decisions). The AI can write to it with the
   "remember" command and it is injected into every new session.
"""

import json
from pathlib import Path
from datetime import datetime

MEM_DIR = Path(__file__).with_name("memory")
HISTORY_FILE = MEM_DIR / "history.json"
NOTES_FILE = MEM_DIR / "notes.md"

# Keep the conversation from growing forever. We always keep the system
# message + the most recent N turns when saving/loading.
MAX_TURNS = 200


def _ensure_dir():
    MEM_DIR.mkdir(parents=True, exist_ok=True)


def load_history():
    """Return the saved message list, or [] if there is none."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(messages):
    """Persist the conversation (trimmed to a sane length)."""
    _ensure_dir()
    if not messages:
        return
    system = [m for m in messages[:1] if m.get("role") == "system"]
    rest = messages[len(system):]
    if len(rest) > MAX_TURNS:
        rest = rest[-MAX_TURNS:]
    try:
        HISTORY_FILE.write_text(json.dumps(system + rest, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[memory] could not save history: {e}")


def clear_history():
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


def load_notes() -> str:
    """Return the long-term notes as text (empty string if none)."""
    if not NOTES_FILE.exists():
        return ""
    try:
        return NOTES_FILE.read_text(encoding="utf-8")
    except Exception:
        return ""


def remember(note: str) -> str:
    """Append a durable fact to long-term memory."""
    _ensure_dir()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"- ({stamp}) {note.strip()}\n"
    try:
        with NOTES_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        return f"ERROR saving note: {e}"
    return f"OK: remembered -> {note.strip()}"
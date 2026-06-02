# OSGPT — Local AI Computer Assistant (Jarvis-style)

A small, cross-platform AI agent split into clean modules. You give it a goal
in plain language; it talks to an LLM via **OpenRouter** and autonomously runs:

```
User → AI → COMMAND → Execute → Result → AI → ... → TASK COMPLETE
```

## Files

| File | What it does |
|------|--------------|
| `config.py`  | Your API key, the model, and the system prompt. **Edit this first.** |
| `ai.py`      | Talks to OpenRouter and parses the AI's JSON command. |
| `execute.py` | Runs the commands the AI sends (make folder, write file, run shell, etc). |
| `memory.py`  | Persistent memory — reloads past chats + keeps long-term notes. |
| `main.py`    | The entry point + the loop that ties it all together. |

## Setup

```bash
pip install requests
```
(Termux: `pkg install python` then `pip install requests`.)

Open `config.py` and paste your OpenRouter key:
```python
API_KEY = "sk-or-..."
```
(or set the env var `OPENROUTER_API_KEY` instead).

## Run

```bash
python main.py                              # interactive
python main.py "create a folder demo with an index.html that says Hello"
```

Add `--auto` to skip the confirmation prompt for `run_command` / `delete`.

## Commands the AI can use
`list_dir`, `read_file`, `write_file`, `make_dir`, `delete`, `change_dir`, `run_command`, `remember`.

## Memory
OSGPT remembers across sessions. Stored in a `memory/` folder created next to the code:
- `memory/history.json` — your conversation, reloaded on startup so it picks up where you left off.
- `memory/notes.md` — durable facts the AI saves with the `remember` command, injected every session.

Type `forget` in interactive mode to wipe the conversation history.

## God mode
The system prompt in `config.py` puts OSGPT in "God mode": when you ask it to build a project,
app, or website it scaffolds a full modern, 2026-grade, production-quality result (real structure,
design system, responsive + animated UI, real content) instead of a basic single page.

To add a new command: write the function in `execute.py`, add it to the
`COMMANDS` dict, and describe it in `SYSTEM_PROMPT` inside `config.py`.

## Safety
This runs real commands on your machine. Keep confirmations on (don't use
`--auto`) until you trust a workflow, and experiment in a scratch folder.

Works on **Linux, Windows, macOS and Termux/Android**.
```
#!/usr/bin/env python3
"""
main.py — OSGPT entry point.

Ties everything together and runs the autonomous loop:

    User -> AI -> COMMAND -> Execute -> Result -> AI -> ... -> TASK COMPLETE

Run:
    python main.py                       (interactive)
    python main.py "create folder demo"  (one-shot)

Options:
    --auto   auto-approve run_command / delete without asking
"""

import sys
import json
import argparse

import config
import ai
import execute
import memory


def run_task(user_request, messages, auto_approve):
    messages.append({"role": "user", "content": user_request})

    for _ in range(config.MAX_STEPS):
        try:
            reply = ai.call_ai(messages)
        except Exception as e:
            print(f"\n[AI error] {e}")
            return

        messages.append({"role": "assistant", "content": reply})

        try:
            cmd = ai.parse_command(reply)
        except Exception as e:
            print(f"\n[parse error] {e}")
            messages.append({
                "role": "user",
                "content": "Your last reply was not valid JSON. Reply with a single JSON object only.",
            })
            continue

        thought = cmd.get("thought", "")
        action = cmd.get("action", "")

        if thought:
            print(f"\n\033[90m[thought] {thought}\033[0m")

        if action == "done":
            print(f"\n\033[92mTASK COMPLETE\033[0m\n{cmd.get('message', '')}")
            return

        args = cmd.get("args", {}) or {}
        print(f"\033[96m[command] {action} {json.dumps(args, ensure_ascii=False)}\033[0m")

        # Confirm potentially destructive commands.
        if not auto_approve and action in execute.DANGEROUS:
            ans = input("  Execute? [y/N] ").strip().lower()
            if ans != "y":
                print("  skipped.")
                messages.append({"role": "user",
                                 "content": "Tool result:\nUser declined to execute this command."})
                continue

        result = execute.execute(action, args)

        preview = result if len(result) < 600 else result[:600] + " ...[truncated in view]"
        print(f"\033[93m[result]\033[0m {preview}")

        messages.append({"role": "user", "content": f"Tool result:\n{result}"})
        memory.save_history(messages)

    print("\n[stopped] Reached the maximum number of steps for this task.")


def main():
    parser = argparse.ArgumentParser(description="OSGPT - local AI computer assistant")
    parser.add_argument("--auto", action="store_true",
                        help="auto-approve run_command/delete without asking")
    parser.add_argument("request", nargs="*", help="one-shot request (otherwise interactive)")
    args = parser.parse_args()

    if not config.have_api_key():
        print(config.api_key_help())
        sys.exit(1)

    # Build the system message: prompt + machine info + long-term notes.
    system_content = config.SYSTEM_PROMPT + "\n\nMachine info:\n" + ai.env_summary()
    notes = memory.load_notes()
    if notes:
        system_content += "\n\nLong-term memory (things you were told to remember):\n" + notes
    messages = [{"role": "system", "content": system_content}]

    # Reload prior conversation so OSGPT remembers past sessions.
    saved = memory.load_history()
    if saved:
        # keep the fresh system message, append the old non-system turns
        messages += [m for m in saved if m.get("role") != "system"]

    print("\033[1mOSGPT\033[0m - local AI computer assistant")
    print(f"Model: {config.MODEL}")
    print(ai.env_summary())
    if saved:
        print(f"(memory: reloaded {len(saved)} past messages — type 'forget' to wipe it)")
    if not args.auto:
        print("(run_command/delete will ask for confirmation; use --auto to skip)")
    print("-" * 60)

    if args.request:
        run_task(" ".join(args.request), messages, args.auto)
        memory.save_history(messages)
        return

    print("Type your request. Type 'exit' or 'quit' to leave.\n")
    while True:
        try:
            user_request = input("\033[1myou>\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break
        if not user_request:
            continue
        if user_request.lower() in ("exit", "quit"):
            print("bye.")
            break
        if user_request.lower() == "forget":
            memory.clear_history()
            print("(memory: conversation history wiped)")
            continue
        run_task(user_request, messages, args.auto)
        memory.save_history(messages)
        print("-" * 60)


if __name__ == "__main__":
    main()
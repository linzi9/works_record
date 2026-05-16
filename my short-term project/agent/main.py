"""
main.py -- CLI entry point for qing-agent.

Reads user input, feeds into agent_loop, displays responses.
"""

import os
import sys

from agent import agent_loop

BANNER = (
    "\033[36m==============================================\n"
    "  qing-agent -- Meta-Agent Builder\n"
    "  21 tools | Memory + Task + Background\n"
    "  Type 'q' or 'exit' to quit\n"
    "==============================================\033[0m"
)


def check_api_key():
    """Check that ANTHROPIC_API_KEY is set before starting."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or key.startswith("sk-") is False:
        print("\033[31mError: ANTHROPIC_API_KEY is not set or invalid.\033[0m")
        print("Copy .env to .env and set your API key:")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        return False
    return True


def display_response(history: list):
    """Print the last assistant text response from history."""
    last = history[-1]["content"]
    if isinstance(last, str):
        print(last)
    elif isinstance(last, list):
        for block in last:
            text = getattr(block, "text", None) or (
                block.get("text") if isinstance(block, dict) else None
            )
            if text:
                print(text)


def main():
    if not check_api_key():
        sys.exit(1)

    print(BANNER)

    history = []
    while True:
        try:
            query = input("\033[32mqing >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if query.strip().lower() in ("q", "exit", ""):
            break

        try:
            history.append({"role": "user", "content": query})
            agent_loop(history)
        except Exception as e:
            print(f"\033[31mError: {e}\033[0m")
            # Remove the failed user message to keep history clean
            if history and history[-1]["role"] == "user":
                history.pop()
            continue

        display_response(history)
        print()


if __name__ == "__main__":
    main()

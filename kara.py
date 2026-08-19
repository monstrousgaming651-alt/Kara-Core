"""Kara Core - CLI entrypoint for Kara-Core v0.1."""
from typing import Optional
import os
from config.loader import load_config
from core.assistant import KaraAssistant, MissingAPIKeyError


def main() -> None:
    """Start the Kara CLI loop."""
    config = load_config()
    name = config.assistant_name or "Kara"

    print(f"{name}: Online.")
    print(f"{name}: Core initialized.")
    print(f"{name}: Awaiting your command. Type 'exit' to shut down.")

    try:
        assistant = KaraAssistant(model=config.model)
    except MissingAPIKeyError as e:
        print(f"Kara: {e}")
        print("Kara: Please set OPENAI_API_KEY in the environment and restart.")
        return

    while True:
        try:
            command = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nKara: Shutting down safely.")
            break

        cmd = command.strip()
        if not cmd:
            continue

        if cmd.lower() in {"exit", "quit", "shutdown"}:
            print("Kara: Shutting down safely.")
            break

        if cmd.lower() == "reset":
            assistant.reset()
            print("Kara: Conversation state cleared.")
            continue

        try:
            reply = assistant.send_message(cmd)
        except Exception as e:
            print(f"Kara: An error occurred while contacting the AI: {e}")
            reply = "(error) I could not process that request."

        print(f"Kara: {reply}")


if __name__ == "__main__":
    main()

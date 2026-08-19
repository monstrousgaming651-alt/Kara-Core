"""Kara Core - first runnable assistant shell (refactored CLI)."""
from typing import Optional
import os
from config.loader import load_config
from core.assistant import KaraAssistant, MissingAPIKeyError


def main() -> None:
    """Start the Kara CLI loop.

    Runs in interactive mode, accepts commands until exit/quit/shutdown.
    """
    config = load_config()
    name = config.assistant_name or "Kara"

    print(f"{name}: Online.")
    print(f"{name}: Core initialized.")
    print(f"{name}: Awaiting your command. Type 'exit' to shut down.")

    try:
        assistant = KaraAssistant(model=config.model, allow_missing_api_key=True)
    except MissingAPIKeyError:
        # Should not happen because allow_missing_api_key=True, but be defensive
        print("Kara: Missing OPENAI_API_KEY and offline mode disabled. Running in local echo mode.")
        assistant = KaraAssistant(model=config.model, allow_missing_api_key=True)

    running = True
    while running:
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

        # Send to assistant and print reply. Handle API errors gracefully.
        try:
            reply = assistant.send_message(cmd)
        except Exception as e:
            print(f"Kara: An error occurred while contacting the AI: {e}")
            reply = f"(error) I could not process that: {cmd}"

        print(f"Kara: {reply}")


if __name__ == "__main__":
    main()

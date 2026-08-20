"""Kara Core - main CLI entry point."""

from __future__ import annotations

from config.loader import load_config
from core.assistant import KaraAssistant, MissingAPIKeyError
from core.engine import KaraEngine
from core.memory import Memory


def main() -> None:
    """Start the Kara CLI."""

    config = load_config()
    name = config.assistant_name or "Kara"

    print(f"{name}: Online.")
    print(f"{name}: Core initialized.")
    print(f"{name}: Awaiting your command. Type 'exit' to shut down.")

    try:
        assistant = KaraAssistant(model=config.model)
        memory = Memory()
        engine = KaraEngine(assistant=assistant, memory=memory)
    except MissingAPIKeyError as exc:
        print(f"{name}: {exc}")
        print(
            f"{name}: Please set OPENAI_API_KEY "
            "in the environment and restart."
        )
        return

    while True:
        try:
            command = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print(f"\n{name}: Shutting down safely.")
            break

        command = command.strip()

        if not command:
            continue

        if command.lower() in {"exit", "quit", "shutdown"}:
            print(f"{name}: Shutting down safely.")
            break

        if command.lower() == "reset":
            assistant.reset()
            print(f"{name}: Conversation state cleared.")
            continue

        try:
            result = engine.process(command)
            print(f"{name}: {result.text}")
        except Exception as exc:
            print(f"{name}: An error occurred: {exc}")


if __name__ == "__main__":
    main()

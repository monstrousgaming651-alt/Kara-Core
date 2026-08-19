"""Kara Core - first runnable assistant shell."""

from datetime import datetime


class Kara:
    """Minimal foundation for the Kara personal AI."""

    def __init__(self, name: str = "Kara") -> None:
        self.name = name
        self.running = True

    def greet(self) -> None:
        print(f"{self.name}: Online.")
        print(
            f"{self.name}: Core initialized at "
            f"{datetime.now():%Y-%m-%d %H:%M:%S}."
        )
        print(
            f"{self.name}: Awaiting your command. "
            "Type 'exit' to shut down."
        )

    def respond(self, command: str) -> str:
        command = command.strip()

        if not command:
            return "I'm listening."

        if command.lower() in {"hello", "hi", "hey"}:
            return "Hello. Kara is online."

        if command.lower() in {"status", "system status"}:
            return "Core status: ONLINE."

        return f"I received: {command}"

    def run(self) -> None:
        self.greet()

        while self.running:
            try:
                command = input("You: ")
            except (EOFError, KeyboardInterrupt):
                print("\nKara: Shutting down safely.")
                break

            if command.strip().lower() in {
                "exit",
                "quit",
                "shutdown",
            }:
                self.running = False
                print("Kara: Shutting down safely.")
                continue

            print(f"Kara: {self.respond(command)}")


if __name__ == "__main__":
    Kara().run()
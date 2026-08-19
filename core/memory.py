"""Persistent memory system for Kara-Core."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Memory:
    """Simple JSON-backed persistent memory."""

    def __init__(self, path: str = "data/memory.json") -> None:
        self.path = Path(path)
        self.data: dict[str, Any] = {}

        self._load()

    def _load(self) -> None:
        """Load memory from disk."""

        if not self.path.exists():
            return

        try:
            with self.path.open("r", encoding="utf-8") as file:
                self.data = json.load(file)
        except (json.JSONDecodeError, OSError):
            self.data = {}

    def _save(self) -> None:
        """Save memory to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                self.data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def set(self, key: str, value: Any) -> None:
        """Store a value in memory."""

        self.data[key] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory."""

        return self.data.get(key, default)

    def delete(self, key: str) -> bool:
        """Delete a memory entry."""

        if key not in self.data:
            return False

        del self.data[key]
        self._save()

        return True

    def clear(self) -> None:
        """Erase all stored memory."""

        self.data.clear()
        self._save()

    def all(self) -> dict[str, Any]:
        """Return all stored memories."""

        return dict(self.data)
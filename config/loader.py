"""Configuration loader for Kara-Core.

Loads config/settings.json and exposes a small typed Config dataclass. Secrets
(e.g., OPENAI_API_KEY) are intentionally not stored here and must come from the
environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json
import os
from pathlib import Path


@dataclass
class Config:
    assistant_name: str = "Kara"
    voice_enabled: bool = False
    interface_enabled: bool = False
    tools_enabled: bool = False
    model: str = "gpt-5.6"


def _default_config_path() -> Path:
    here = Path(__file__).resolve().parent
    return here / "settings.json"


def load_config(path: Optional[str] = None) -> Config:
    """Load configuration from settings.json.

    Args:
        path: Optional path to a JSON settings file. If omitted, uses
            config/settings.json next to this loader.

    Returns:
        Config: the loaded configuration with environment overrides applied.
    """
    cfg = Config()
    config_path = Path(path) if path else _default_config_path()

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            cfg.assistant_name = data.get("assistant_name", cfg.assistant_name)
            cfg.voice_enabled = bool(data.get("voice_enabled", cfg.voice_enabled))
            cfg.interface_enabled = bool(data.get("interface_enabled", cfg.interface_enabled))
            cfg.tools_enabled = bool(data.get("tools_enabled", cfg.tools_enabled))
            cfg.model = data.get("model", cfg.model)
        except Exception:
            # If parsing fails, return defaults to avoid crashing the loader.
            pass

    # Allow environment overrides for model (KARA_MODEL). Do not allow API keys here.
    env_model = os.environ.get("KARA_MODEL")
    if env_model:
        cfg.model = env_model

    return cfg

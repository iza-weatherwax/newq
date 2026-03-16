"""
config/settings.py — Preferências do usuário persistidas entre sessões.
Salvo em ~/.email_builder/settings.json
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


_SETTINGS_PATH = Path.home() / ".email_builder" / "settings.json"


@dataclass
class AppSettings:
    last_open_dir: str = str(Path.home())
    default_font_size: int = 14
    canvas_width: int = 600
    chart_dpi: int = 96
    undo_limit: int = 50
    snap_to_grid: bool = True

    # ------------------------------------------------------------------ #
    # Persistência
    # ------------------------------------------------------------------ #

    def save(self) -> None:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "AppSettings":
        if not _SETTINGS_PATH.exists():
            return cls()
        try:
            data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
            return cls(
                last_open_dir=data.get("last_open_dir", str(Path.home())),
                default_font_size=data.get("default_font_size", 14),
                canvas_width=data.get("canvas_width", 600),
                chart_dpi=data.get("chart_dpi", 96),
                undo_limit=data.get("undo_limit", 50),
                snap_to_grid=data.get("snap_to_grid", True),
            )
        except (json.JSONDecodeError, KeyError):
            return cls()

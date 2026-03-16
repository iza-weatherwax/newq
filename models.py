"""
models.py — Dataclasses tipadas que servem como contrato entre todas as camadas.
Importar daqui evita drift silencioso via dict sem tipagem.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# DataBlock — produzido pelo data_engine, consumido pelo compilador HTML
# ---------------------------------------------------------------------------

@dataclass
class DataBlock:
    block_id: str
    block_type: str          # 'kpi' | 'table' | 'chart'
    title: str
    data: Any                # dict (kpi/chart) ou pd.DataFrame (table)
    config: dict             # parâmetros usados para criar o bloco
    source_file: str = ""    # caminho absoluto do arquivo de dados
    source_hash: str = ""    # SHA-256 do arquivo (detecta alterações)

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex[:8]

    def to_dict(self) -> dict:
        import pandas as pd
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "title": self.title,
            "data": self.data if not isinstance(self.data, pd.DataFrame) else "__dataframe__",
            "config": self.config,
            "source_file": self.source_file,
            "source_hash": self.source_hash,
        }


# ---------------------------------------------------------------------------
# BlockConfig — estado de cada widget no canvas
# ---------------------------------------------------------------------------

@dataclass
class BlockConfig:
    block_id: str
    block_type: str          # 'kpi' | 'table' | 'chart_bar' | 'text' | 'divider' | 'spacer' | ...
    title: str = ""
    bg_color: str = "#ffffff"
    header_color: str = "#2c3e50"
    text_color: str = "#333333"
    font_size: int = 14
    data_block_id: str | None = None
    text_body: str = ""
    pos: dict = field(default_factory=lambda: {"x": 0, "y": 0})
    size: dict = field(default_factory=lambda: {"w": 200, "h": 120})

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex[:8]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BlockConfig":
        return cls(
            block_id=d.get("block_id", cls.new_id()),
            block_type=d.get("block_type", "text"),
            title=d.get("title", ""),
            bg_color=d.get("bg_color", "#ffffff"),
            header_color=d.get("header_color", "#2c3e50"),
            text_color=d.get("text_color", "#333333"),
            font_size=d.get("font_size", 14),
            data_block_id=d.get("data_block_id"),
            text_body=d.get("text_body", ""),
            pos=d.get("pos", {"x": 0, "y": 0}),
            size=d.get("size", {"w": 200, "h": 120}),
        )


# ---------------------------------------------------------------------------
# LayoutMeta + Layout — schema do arquivo JSON de layout
# ---------------------------------------------------------------------------

@dataclass
class LayoutMeta:
    version: str = "1.0"
    saved_at: str = ""
    block_count: int = 0
    source_file: str = ""    # último arquivo de dados carregado
    source_hash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "LayoutMeta":
        return cls(
            version=d.get("version", "1.0"),
            saved_at=d.get("saved_at", ""),
            block_count=d.get("block_count", 0),
            source_file=d.get("source_file", ""),
            source_hash=d.get("source_hash", ""),
        )


@dataclass
class Layout:
    meta: LayoutMeta = field(default_factory=LayoutMeta)
    blocks: list[BlockConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "_meta": self.meta.to_dict(),
            "blocks": [b.to_dict() for b in self.blocks],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Layout":
        meta = LayoutMeta.from_dict(d.get("_meta", {}))
        blocks = [BlockConfig.from_dict(b) for b in d.get("blocks", [])]
        return cls(meta=meta, blocks=blocks)

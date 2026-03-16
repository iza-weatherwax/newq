"""
tests/test_layout_manager.py — Testa save/load e migração de schema.
"""
import json
from pathlib import Path

import pytest

from email_builder.layout_manager.manager import (
    CURRENT_VERSION,
    empty_layout,
    load_layout,
    save_layout,
)
from email_builder.models import BlockConfig, Layout, LayoutMeta


def _sample_layout() -> Layout:
    meta = LayoutMeta(source_file="/data/report.xlsx", source_hash="abc")
    blocks = [
        BlockConfig(
            block_id="aabb1122",
            block_type="kpi",
            title="Total",
            pos={"x": 0, "y": 0},
            size={"w": 200, "h": 120},
        ),
        BlockConfig(
            block_id="ccdd3344",
            block_type="text",
            title="Intro",
            text_body="Olá!",
            pos={"x": 0, "y": 140},
            size={"w": 600, "h": 80},
        ),
    ]
    return Layout(meta=meta, blocks=blocks)


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "layout.json"
    layout = _sample_layout()
    save_layout(str(path), layout)

    loaded = load_layout(str(path))
    assert len(loaded.blocks) == 2
    assert loaded.blocks[0].block_id == "aabb1122"
    assert loaded.blocks[1].text_body == "Olá!"


def test_saved_json_has_meta(tmp_path):
    path = tmp_path / "layout.json"
    save_layout(str(path), _sample_layout())

    data = json.loads(path.read_text())
    assert "_meta" in data
    assert data["_meta"]["version"] == CURRENT_VERSION
    assert data["_meta"]["block_count"] == 2
    assert data["_meta"]["saved_at"] != ""


def test_load_missing_meta(tmp_path):
    path = tmp_path / "layout.json"
    path.write_text(json.dumps({"blocks": []}))
    layout = load_layout(str(path))
    assert layout.blocks == []


def test_empty_layout():
    layout = empty_layout()
    assert layout.blocks == []
    assert layout.meta.version == CURRENT_VERSION


def test_block_config_roundtrip():
    cfg = BlockConfig(
        block_id="test1234",
        block_type="chart_bar",
        title="Vendas",
        bg_color="#ff0000",
        data_block_id="data5678",
        pos={"x": 100, "y": 200},
        size={"w": 400, "h": 200},
    )
    d = cfg.to_dict()
    restored = BlockConfig.from_dict(d)
    assert restored.block_id == "test1234"
    assert restored.bg_color == "#ff0000"
    assert restored.data_block_id == "data5678"
    assert restored.pos == {"x": 100, "y": 200}

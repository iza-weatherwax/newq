"""
tests/test_compiler.py — Testa a compilação HTML por tipo de bloco.
"""
import pandas as pd
import pytest

from email_builder.html_compiler.compiler import compile_canvas
from email_builder.html_compiler.validator import validate_layout
from email_builder.models import BlockConfig, DataBlock


def _cfg(block_type: str, **kwargs) -> dict:
    c = BlockConfig(
        block_id=BlockConfig.new_id(),
        block_type=block_type,
        title=block_type.upper(),
        pos={"x": 0, "y": 0},
        size={"w": 600, "h": 120},
        **kwargs,
    )
    return c.to_dict()


def _kpi_block() -> DataBlock:
    return DataBlock(
        block_id="test0001",
        block_type="kpi",
        title="Total",
        data={"value": 42.0, "formatted": "42", "label": "Total"},
        config={},
    )


def _table_block() -> DataBlock:
    return DataBlock(
        block_id="test0002",
        block_type="table",
        title="Tabela",
        data=pd.DataFrame({"A": [1, 2], "B": [3, 4]}),
        config={},
    )


# ---------------------------------------------------------------------------

def test_compile_empty_canvas():
    html = compile_canvas([], {})
    assert "<!DOCTYPE html>" in html
    assert "<table" in html


def test_compile_kpi_block():
    db = _kpi_block()
    cfg = _cfg("kpi", data_block_id=db.block_id)
    html = compile_canvas([cfg], {db.block_id: db})
    assert "42" in html
    assert "KPI" in html


def test_compile_table_block():
    db = _table_block()
    cfg = _cfg("table", data_block_id=db.block_id)
    html = compile_canvas([cfg], {db.block_id: db})
    assert "<table" in html
    assert "thead" in html.lower() or "<th" in html


def test_compile_text_block():
    cfg = _cfg("text", text_body="Olá, mundo!")
    html = compile_canvas([cfg], {})
    assert "Olá, mundo!" in html


def test_compile_divider():
    cfg = _cfg("divider")
    html = compile_canvas([cfg], {})
    assert "border-top" in html


def test_compile_spacer():
    cfg = _cfg("spacer")
    cfg["size"] = {"w": 600, "h": 30}
    html = compile_canvas([cfg], {})
    assert "30px" in html


def test_missing_data_block_raises():
    cfg = _cfg("kpi", data_block_id="nonexistent")
    with pytest.raises(ValueError, match="nonexistent"):
        compile_canvas([cfg], {})


def test_html_has_boilerplate():
    html = compile_canvas([], {})
    assert "<!DOCTYPE html>" in html
    assert 'width="600"' in html
    assert "</html>" in html


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def test_validator_empty_canvas():
    errors = validate_layout([])
    assert any("vazio" in e.lower() for e in errors)


def test_validator_kpi_without_data_block():
    cfg = _cfg("kpi")  # sem data_block_id
    errors = validate_layout([cfg])
    assert any("DataBlock" in e for e in errors)


def test_validator_ok_with_data_block():
    cfg = _cfg("text")  # text não precisa de DataBlock
    errors = validate_layout([cfg])
    assert errors == []


def test_validator_overlap():
    a = _cfg("kpi")
    b = _cfg("table")
    # Mesma posição = 100% sobreposição
    a["pos"] = {"x": 0, "y": 0}
    b["pos"] = {"x": 0, "y": 0}
    a["size"] = {"w": 200, "h": 100}
    b["size"] = {"w": 200, "h": 100}
    errors = validate_layout([a, b])
    assert any("sobreposição" in e.lower() for e in errors)

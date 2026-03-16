"""
tests/test_loader.py — Testa o DataLoader com arquivos de fixture.
"""
import csv
import io
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from email_builder.data_engine.loader import DataLoader


def _make_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _make_xlsx(data: dict[str, list[dict]], path: Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, rows in data.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet, index=False)


# ---------------------------------------------------------------------------

def test_load_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    _make_csv([{"Nome": "Alice", "Vendas": 100}, {"Nome": "Bob", "Vendas": 200}], csv_file)

    loader = DataLoader(str(csv_file))
    sheets = loader.load()

    assert "Sheet1" in sheets
    df = sheets["Sheet1"]
    assert list(df.columns) == ["Nome", "Vendas"]
    assert len(df) == 2
    assert loader.source_hash != ""


def test_load_xlsx_multi_sheet(tmp_path):
    pytest.importorskip("openpyxl", reason="openpyxl não instalado")
    xlsx_file = tmp_path / "data.xlsx"
    _make_xlsx(
        {
            "Vendas": [{"Produto": "A", "Total": 500}],
            "Clientes": [{"Nome": "Alice"}, {"Nome": "Bob"}],
        },
        xlsx_file,
    )

    loader = DataLoader(str(xlsx_file))
    sheets = loader.load()

    assert "Vendas" in sheets
    assert "Clientes" in sheets
    assert sheets["Vendas"]["Total"].iloc[0] == 500
    assert len(sheets["Clientes"]) == 2


def test_load_unsupported_extension(tmp_path):
    bad_file = tmp_path / "data.json"
    bad_file.write_text('{"a": 1}')
    with pytest.raises(ValueError, match="Formato não suportado"):
        DataLoader(str(bad_file)).load()


def test_source_hash_changes_when_file_changes(tmp_path):
    csv_file = tmp_path / "data.csv"
    _make_csv([{"x": 1}], csv_file)
    h1 = DataLoader(str(csv_file)).source_hash

    _make_csv([{"x": 2}], csv_file)
    h2 = DataLoader(str(csv_file)).source_hash

    assert h1 != h2

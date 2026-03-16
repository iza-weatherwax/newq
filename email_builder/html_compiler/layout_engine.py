"""
html_compiler/layout_engine.py — Converte lista de BlockConfig dicts
em linhas e colunas de uma tabela HTML table-based.

Algoritmo:
  1. Ordena blocos por pos.y
  2. Agrupa em "linhas" (tolerância vertical de 20px — GRID)
  3. Dentro de cada linha, ordena por pos.x
  4. Calcula colspan baseado em largura relativa a 600px
"""
from __future__ import annotations

EMAIL_WIDTH = 600
GRID_TOLERANCE = 20  # px — blocos dentro desta faixa de Y são considerados na mesma linha
COL_UNIT = 100       # menor unidade de coluna (600 / 6)


def build_rows(blocks: list[dict]) -> list[list[dict]]:
    """
    Retorna lista de linhas, cada linha sendo lista de blocos ordenados por X.
    """
    if not blocks:
        return []

    sorted_blocks = sorted(blocks, key=lambda b: b.get("pos", {}).get("y", 0))
    rows: list[list[dict]] = []
    current_row: list[dict] = []
    current_y: int = sorted_blocks[0].get("pos", {}).get("y", 0)

    for b in sorted_blocks:
        y = b.get("pos", {}).get("y", 0)
        if abs(y - current_y) <= GRID_TOLERANCE:
            current_row.append(b)
        else:
            if current_row:
                rows.append(sorted(current_row, key=lambda b_: b_.get("pos", {}).get("x", 0)))
            current_row = [b]
            current_y = y

    if current_row:
        rows.append(sorted(current_row, key=lambda b_: b_.get("pos", {}).get("x", 0)))

    return rows


def colspan_for(block: dict) -> int:
    """Calcula colspan (unidades de COL_UNIT) para um bloco."""
    w = block.get("size", {}).get("w", EMAIL_WIDTH)
    cols = max(1, round(w / COL_UNIT))
    return min(cols, EMAIL_WIDTH // COL_UNIT)

"""
html_compiler/validator.py — Valida o layout antes da compilação.
Retorna lista de strings descrevendo os problemas encontrados.
"""
from __future__ import annotations

_DATA_TYPES = {"kpi", "table", "chart_bar", "chart_barh", "chart_line", "chart_pie"}


def validate_layout(blocks: list[dict]) -> list[str]:
    """
    Valida a lista de dicts de BlockConfig.
    Retorna lista de mensagens de erro/aviso (vazia = tudo ok).
    """
    errors: list[str] = []

    if not blocks:
        errors.append("O canvas está vazio — adicione ao menos um bloco.")
        return errors

    for b in blocks:
        bt = b.get("block_type", "")
        title = b.get("title") or bt
        if bt in _DATA_TYPES and not b.get("data_block_id"):
            errors.append(
                f"Bloco '{title}' ({bt}) não tem DataBlock vinculado. "
                "Vincule um DataBlock no painel de propriedades."
            )

    # Verifica sobreposição excessiva (>50% de área)
    for i, a in enumerate(blocks):
        for j, b_ in enumerate(blocks):
            if i >= j:
                continue
            overlap = _overlap_area(a, b_)
            area_a = a.get("size", {}).get("w", 0) * a.get("size", {}).get("h", 0)
            if area_a and overlap / area_a > 0.5:
                errors.append(
                    f"Blocos '{a.get('title') or a.get('block_type')}' e "
                    f"'{b_.get('title') or b_.get('block_type')}' têm sobreposição excessiva."
                )

    return errors


def _overlap_area(a: dict, b: dict) -> int:
    ax, ay = a.get("pos", {}).get("x", 0), a.get("pos", {}).get("y", 0)
    aw, ah = a.get("size", {}).get("w", 0), a.get("size", {}).get("h", 0)
    bx, by = b.get("pos", {}).get("x", 0), b.get("pos", {}).get("y", 0)
    bw, bh = b.get("size", {}).get("w", 0), b.get("size", {}).get("h", 0)

    ox = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    oy = max(0, min(ay + ah, by + bh) - max(ay, by))
    return ox * oy

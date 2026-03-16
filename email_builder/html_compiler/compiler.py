"""
html_compiler/compiler.py — Orquestra validator → layout_engine → renderers
para produzir HTML table-based Outlook-safe (600px).
"""
from __future__ import annotations

from email_builder.html_compiler.layout_engine import build_rows, colspan_for, EMAIL_WIDTH, COL_UNIT
from email_builder.html_compiler.renderers import _renderers, TextRenderer
from email_builder.models import DataBlock

_BOILERPLATE_TOP = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Email</title>
</head>
<body style="margin:0; padding:0; background:#f5f5f5; font-family:Arial,Helvetica,sans-serif;">
<table width="600" cellpadding="0" cellspacing="0" border="0"
       align="center" style="max-width:600px; background:#ffffff;">
"""

_BOILERPLATE_BOTTOM = """\
</table>
</body>
</html>
"""


def compile_canvas(
    block_configs: list[dict],
    data_blocks: dict[str, DataBlock],
) -> str:
    """
    Compila o estado do canvas em HTML.

    Args:
        block_configs: lista de BlockConfig.to_dict()
        data_blocks: dicionário {data_block_id: DataBlock}

    Returns:
        String HTML completa.

    Raises:
        ValueError: se um data_block_id referenciado não existir.
    """
    rows = build_rows(block_configs)
    html_rows: list[str] = []

    for row in rows:
        cells: list[str] = []
        for block in row:
            bt = block.get("block_type", "text")
            db_id = block.get("data_block_id")
            db: DataBlock | None = None

            if db_id:
                if db_id not in data_blocks:
                    raise ValueError(
                        f"DataBlock '{db_id}' não encontrado. "
                        "Recarregue o arquivo de dados e recrie as agregações."
                    )
                db = data_blocks[db_id]

            renderer = _renderers.get(bt, TextRenderer())
            inner_html = renderer.render(block, db)

            colspan = colspan_for(block)
            cells.append(
                f'<td valign="top" colspan="{colspan}" '
                f'style="padding:4px; vertical-align:top;">'
                f'{inner_html}'
                f'</td>'
            )

        # Preenche colunas restantes para totalizar EMAIL_WIDTH
        used_cols = sum(colspan_for(b) for b in row)
        total_cols = EMAIL_WIDTH // COL_UNIT
        if used_cols < total_cols:
            cells.append(
                f'<td colspan="{total_cols - used_cols}" style="padding:0;"></td>'
            )

        html_rows.append(f'  <tr valign="top">{"".join(cells)}</tr>\n')

    return _BOILERPLATE_TOP + "".join(html_rows) + _BOILERPLATE_BOTTOM

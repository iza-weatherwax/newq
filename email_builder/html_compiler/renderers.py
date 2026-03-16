"""
html_compiler/renderers.py — Um renderer por tipo de bloco.
Interface: render(config: dict, data_block: DataBlock | None) -> str (HTML)
"""
from __future__ import annotations

import base64
import hashlib
import io
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from email_builder.models import DataBlock

# Cache simples de imagens geradas: (data_block_id, config_hash) → base64
_IMG_CACHE: dict[tuple[str, str], str] = {}

_FONT = "Arial, Helvetica, sans-serif"
_EMAIL_WIDTH = 600


def _config_hash(config: dict) -> str:
    import json
    return hashlib.md5(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()[:12]


class BlockRenderer(ABC):
    @abstractmethod
    def render(self, config: dict, data_block: DataBlock | None) -> str:
        ...


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------

class KPIRenderer(BlockRenderer):
    def render(self, config: dict, data_block: DataBlock | None) -> str:
        bg = config.get("bg_color", "#ffffff")
        hdr = config.get("header_color", "#2c3e50")
        txt = config.get("text_color", "#333333")
        title = config.get("title", "KPI")
        font_size = config.get("font_size", 14)

        if data_block and isinstance(data_block.data, dict):
            value = data_block.data.get("formatted", str(data_block.data.get("value", "—")))
            label = data_block.data.get("label", title)
        else:
            value = "—"
            label = title

        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{bg}; border:1px solid #e0e0e0; border-radius:4px;">
  <tr>
    <td style="background:{hdr}; padding:6px 12px; font-family:{_FONT};
               font-size:12px; font-weight:bold; color:white;">
      {_esc(title)}
    </td>
  </tr>
  <tr>
    <td align="center" style="padding:16px 12px; font-family:{_FONT};">
      <span style="font-size:{font_size * 2}px; font-weight:bold; color:{txt};">
        {_esc(value)}
      </span><br>
      <span style="font-size:{font_size}px; color:#888;">{_esc(label)}</span>
    </td>
  </tr>
</table>"""


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

class TableRenderer(BlockRenderer):
    def render(self, config: dict, data_block: DataBlock | None) -> str:
        bg = config.get("bg_color", "#ffffff")
        hdr = config.get("header_color", "#2c3e50")
        txt = config.get("text_color", "#333333")
        title = config.get("title", "Tabela")
        font_size = config.get("font_size", 12)

        df: pd.DataFrame | None = None
        if data_block and isinstance(data_block.data, pd.DataFrame):
            df = data_block.data

        header_row = ""
        body_rows = ""

        if df is not None and not df.empty:
            cols = [str(c) for c in df.columns]
            header_row = "".join(
                f'<th style="padding:6px 8px; background:{hdr}; color:white;'
                f' font-family:{_FONT}; font-size:{font_size}px; text-align:left;'
                f' white-space:nowrap;">{_esc(c)}</th>'
                for c in cols
            )
            for i, row in enumerate(df.itertuples(index=False)):
                row_bg = bg if i % 2 == 0 else _lighten(bg)
                cells = "".join(
                    f'<td style="padding:5px 8px; font-family:{_FONT};'
                    f' font-size:{font_size}px; color:{txt};">{_esc(str(v))}</td>'
                    for v in row
                )
                body_rows += f'<tr style="background:{row_bg};">{cells}</tr>\n'
        else:
            header_row = f'<th style="color:white;background:{hdr};padding:6px;">(sem dados)</th>'

        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{bg}; border:1px solid #e0e0e0;">
  <tr>
    <td colspan="99" style="background:{hdr}; padding:6px 12px;
        font-family:{_FONT}; font-size:12px; font-weight:bold; color:white;">
      {_esc(title)}
    </td>
  </tr>
  <tr>{header_row}</tr>
  {body_rows}
</table>"""


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

class ChartRenderer(BlockRenderer):
    def __init__(self, dpi: int = 96) -> None:
        self.dpi = dpi

    def render(self, config: dict, data_block: DataBlock | None) -> str:
        bg = config.get("bg_color", "#ffffff")
        hdr = config.get("header_color", "#2c3e50")
        title = config.get("title", "Gráfico")
        block_type = config.get("block_type", "chart_bar")
        w = min(config.get("size", {}).get("w", 400), _EMAIL_WIDTH)

        b64 = self._get_image(config, data_block, w)

        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{bg}; border:1px solid #e0e0e0;">
  <tr>
    <td style="background:{hdr}; padding:6px 12px;
        font-family:{_FONT}; font-size:12px; font-weight:bold; color:white;">
      {_esc(title)}
    </td>
  </tr>
  <tr>
    <td align="center" style="padding:8px;">
      <img src="data:image/png;base64,{b64}" width="{w}"
           style="display:block; border:0;" alt="{_esc(title)}">
    </td>
  </tr>
</table>"""

    def _get_image(self, config: dict, data_block: DataBlock | None, width: int) -> str:
        if data_block is None:
            return _placeholder_b64(width, 80)

        cache_key = (data_block.block_id, _config_hash(config))
        if cache_key in _IMG_CACHE:
            return _IMG_CACHE[cache_key]

        b64 = self._generate(config, data_block, width)
        _IMG_CACHE[cache_key] = b64
        return b64

    def _generate(self, config: dict, data_block: DataBlock, width: int) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_type = config.get("block_type", "chart_bar").replace("chart_", "")
        data = data_block.data

        df: pd.DataFrame | None = None
        x_col = y_col = None

        if isinstance(data, dict):
            df = data.get("df")
            x_col = data.get("x")
            y_col = data.get("y")
        elif isinstance(data, pd.DataFrame):
            df = data

        if df is None or df.empty:
            return _placeholder_b64(width, 80)

        fig_w = width / self.dpi
        fig_h = max(1.5, fig_w * 0.5)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=self.dpi)
        color = config.get("color", data_block.config.get("color", "#4285f4"))

        try:
            if chart_type == "pie":
                if y_col and y_col in df.columns:
                    labels = df[x_col].astype(str) if x_col and x_col in df.columns else None
                    ax.pie(df[y_col], labels=labels, autopct="%1.0f%%", colors=None)
                else:
                    ax.text(0.5, 0.5, "Sem dados", ha="center", va="center")
            elif chart_type == "barh":
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    ax.barh(df[x_col].astype(str), df[y_col], color=color)
                else:
                    ax.barh(df.iloc[:, 0].astype(str), df.iloc[:, 1] if len(df.columns) > 1 else [0], color=color)
            elif chart_type == "line":
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    ax.plot(df[x_col].astype(str), df[y_col], color=color, marker="o", markersize=4)
                else:
                    ax.plot(df.iloc[:, 0].astype(str), df.iloc[:, 1] if len(df.columns) > 1 else [0], color=color)
                ax.tick_params(axis="x", rotation=30)
            else:  # bar
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    ax.bar(df[x_col].astype(str), df[y_col], color=color)
                else:
                    ax.bar(df.iloc[:, 0].astype(str), df.iloc[:, 1] if len(df.columns) > 1 else [0], color=color)
                ax.tick_params(axis="x", rotation=30)

            ax.set_title(config.get("title", ""), fontsize=9, pad=4)
            ax.tick_params(labelsize=7)
            fig.tight_layout()
        except Exception:
            ax.text(0.5, 0.5, "Erro ao gerar gráfico", ha="center", va="center", transform=ax.transAxes)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

class TextRenderer(BlockRenderer):
    def render(self, config: dict, data_block: DataBlock | None) -> str:
        bg = config.get("bg_color", "#ffffff")
        txt = config.get("text_color", "#333333")
        font_size = config.get("font_size", 14)
        body = config.get("text_body", "")
        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{bg};">
  <tr>
    <td style="padding:12px 16px; font-family:{_FONT};
               font-size:{font_size}px; color:{txt}; line-height:1.5;">
      {_nl2br(_esc(body))}
    </td>
  </tr>
</table>"""


# ---------------------------------------------------------------------------
# Divider
# ---------------------------------------------------------------------------

class DividerRenderer(BlockRenderer):
    def render(self, config: dict, data_block: DataBlock | None) -> str:
        return """
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td style="padding:8px 0; border-top:1px solid #e0e0e0; font-size:1px; line-height:1px;">&nbsp;</td>
  </tr>
</table>"""


# ---------------------------------------------------------------------------
# Spacer
# ---------------------------------------------------------------------------

class SpacerRenderer(BlockRenderer):
    def render(self, config: dict, data_block: DataBlock | None) -> str:
        h = config.get("size", {}).get("h", 20)
        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr><td style="height:{h}px; font-size:1px; line-height:1px;">&nbsp;</td></tr>
</table>"""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_RENDERERS: dict[str, BlockRenderer] = {
    "kpi": KPIRenderer(),
    "table": TableRenderer(),
    "chart_bar": ChartRenderer(),
    "chart_barh": ChartRenderer(),
    "chart_line": ChartRenderer(),
    "chart_pie": ChartRenderer(),
    "text": TextRenderer(),
    "divider": DividerRenderer(),
    "spacer": SpacerRenderer(),
}


def get_renderer(block_type: str) -> BlockRenderer:
    return _renderers.get(block_type, TextRenderer())


_renderers = _RENDERERS  # alias


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _nl2br(s: str) -> str:
    return s.replace("\n", "<br>")


def _lighten(hex_color: str, amount: float = 0.05) -> str:
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def _placeholder_b64(w: int, h: int) -> str:
    """Imagem placeholder cinza simples."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(w / 96, h / 96), dpi=96)
    ax.text(0.5, 0.5, "Sem dados", ha="center", va="center", color="#999",
            fontsize=8, transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f5f5f5")
    fig.patch.set_facecolor("#f5f5f5")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=96)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

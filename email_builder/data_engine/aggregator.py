"""
data_engine/aggregator.py — Cria DataBlocks a partir de DataFrames pandas.
Operações de agregação enumeradas explicitamente.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

import pandas as pd

from email_builder.models import DataBlock


class AggOp(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MAX = "MAX"
    MIN = "MIN"
    FILTER = "FILTER"
    NONE = "NONE"       # sem agregação — retorna DataFrame inteiro


class DataAggregator:

    def create_block(
        self,
        block_type: str,
        df: pd.DataFrame,
        config: dict,
        source_file: str = "",
        source_hash: str = "",
    ) -> DataBlock:
        """
        Fábrica principal. config keys variam por block_type:
          kpi   → {"column": str, "operation": AggOp, "label": str, "format": str}
          table → {"columns": list[str] | None, "operation": AggOp | None,
                    "group_by": str | None, "max_rows": int | None}
          chart → {"chart_type": str, "x": str, "y": str | list[str],
                    "operation": AggOp | None, "group_by": str | None,
                    "title": str, "color": str}
        """
        if block_type == "kpi":
            data = self._aggregate_kpi(df, config)
        elif block_type == "table":
            data = self._aggregate_table(df, config)
        elif block_type in {"chart_bar", "chart_barh", "chart_line", "chart_pie"}:
            data = self._aggregate_chart(df, config)
        else:
            raise ValueError(f"block_type desconhecido: '{block_type}'")

        return DataBlock(
            block_id=DataBlock.new_id(),
            block_type=block_type,
            title=config.get("title", config.get("label", block_type.upper())),
            data=data,
            config=config,
            source_file=source_file,
            source_hash=source_hash,
        )

    # ------------------------------------------------------------------ #
    # KPI
    # ------------------------------------------------------------------ #

    def _aggregate_kpi(self, df: pd.DataFrame, config: dict) -> dict:
        column = config.get("column")
        operation = AggOp(config.get("operation", AggOp.SUM))
        fmt = config.get("format", "{:,.0f}")
        label = config.get("label", column or "KPI")

        if column and column in df.columns:
            series = df[column]
            # Aplica filtro se configurado
            filters = config.get("filters", [])
            for f in filters:
                col, op, val = f["column"], f["op"], f["value"]
                if op == "==":
                    series = df.loc[df[col] == val, column]
                elif op == "!=":
                    series = df.loc[df[col] != val, column]
                elif op == ">":
                    series = df.loc[df[col] > val, column]
                elif op == "<":
                    series = df.loc[df[col] < val, column]

            raw = self._apply_op(series, operation)
        else:
            raw = 0

        try:
            formatted = fmt.format(raw)
        except (ValueError, KeyError):
            formatted = str(raw)

        return {"value": raw, "formatted": formatted, "label": label}

    # ------------------------------------------------------------------ #
    # Table
    # ------------------------------------------------------------------ #

    def _aggregate_table(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        columns = config.get("columns")
        group_by = config.get("group_by")
        operation = config.get("operation", AggOp.NONE)
        max_rows = config.get("max_rows")

        if columns:
            existing = [c for c in columns if c in df.columns]
            df = df[existing] if existing else df

        if group_by and group_by in df.columns and operation != AggOp.NONE:
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            if group_by in numeric_cols:
                numeric_cols.remove(group_by)
            agg_map = {c: self._pandas_agg(AggOp(operation)) for c in numeric_cols}
            if agg_map:
                df = df.groupby(group_by).agg(agg_map).reset_index()

        if max_rows:
            df = df.head(max_rows)

        return df

    # ------------------------------------------------------------------ #
    # Chart
    # ------------------------------------------------------------------ #

    def _aggregate_chart(self, df: pd.DataFrame, config: dict) -> dict:
        x_col = config.get("x")
        y_col = config.get("y")
        group_by = config.get("group_by")
        operation = config.get("operation", AggOp.NONE)

        if group_by and group_by in df.columns and operation != AggOp.NONE and y_col:
            y_cols = [y_col] if isinstance(y_col, str) else y_col
            agg_map = {c: self._pandas_agg(AggOp(operation)) for c in y_cols if c in df.columns}
            if agg_map:
                df = df.groupby(group_by).agg(agg_map).reset_index()
                if x_col is None:
                    x_col = group_by

        return {
            "df": df,
            "x": x_col,
            "y": y_col,
            "chart_type": config.get("chart_type", "bar"),
            "title": config.get("title", ""),
            "color": config.get("color", "#4285f4"),
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _apply_op(series: pd.Series, op: AggOp) -> Any:
        try:
            s = pd.to_numeric(series, errors="coerce").dropna()
        except Exception:
            return 0
        if op == AggOp.SUM:
            return float(s.sum())
        if op == AggOp.AVG:
            return float(s.mean()) if len(s) else 0
        if op == AggOp.COUNT:
            return int(len(series))
        if op == AggOp.MAX:
            return float(s.max()) if len(s) else 0
        if op == AggOp.MIN:
            return float(s.min()) if len(s) else 0
        return float(s.sum())

    @staticmethod
    def _pandas_agg(op: AggOp) -> str:
        mapping = {
            AggOp.SUM: "sum",
            AggOp.AVG: "mean",
            AggOp.COUNT: "count",
            AggOp.MAX: "max",
            AggOp.MIN: "min",
        }
        return mapping.get(op, "sum")

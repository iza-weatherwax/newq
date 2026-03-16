"""
tests/test_aggregator.py — Testa cada operação de agregação.
"""
import pandas as pd
import pytest

from email_builder.data_engine.aggregator import AggOp, DataAggregator
from email_builder.models import DataBlock


@pytest.fixture
def agg():
    return DataAggregator()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Produto": ["A", "B", "A", "C"],
        "Categoria": ["X", "X", "Y", "Y"],
        "Vendas": [100.0, 200.0, 150.0, 50.0],
        "Qtd": [10, 20, 15, 5],
    })


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------

def test_kpi_sum(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {"column": "Vendas", "operation": "SUM", "label": "Total"})
    assert block.block_type == "kpi"
    assert block.data["value"] == pytest.approx(500.0)


def test_kpi_avg(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {"column": "Vendas", "operation": "AVG"})
    assert block.data["value"] == pytest.approx(125.0)


def test_kpi_count(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {"column": "Vendas", "operation": "COUNT"})
    assert block.data["value"] == 4


def test_kpi_max(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {"column": "Vendas", "operation": "MAX"})
    assert block.data["value"] == pytest.approx(200.0)


def test_kpi_min(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {"column": "Vendas", "operation": "MIN"})
    assert block.data["value"] == pytest.approx(50.0)


def test_kpi_format(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {
        "column": "Vendas", "operation": "SUM", "format": "R$ {:,.2f}"
    })
    assert block.data["formatted"] == "R$ 500.00"


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def test_table_full(agg, sample_df):
    block = agg.create_block("table", sample_df, {})
    assert isinstance(block.data, pd.DataFrame)
    assert len(block.data) == 4


def test_table_groupby_sum(agg, sample_df):
    block = agg.create_block("table", sample_df, {
        "group_by": "Categoria", "operation": "SUM"
    })
    df = block.data
    assert "Categoria" in df.columns
    x_row = df[df["Categoria"] == "X"].iloc[0]
    assert x_row["Vendas"] == pytest.approx(300.0)


def test_table_max_rows(agg, sample_df):
    block = agg.create_block("table", sample_df, {"max_rows": 2})
    assert len(block.data) == 2


# ---------------------------------------------------------------------------
# DataBlock metadata
# ---------------------------------------------------------------------------

def test_datablock_has_source_info(agg, sample_df):
    block = agg.create_block(
        "kpi", sample_df,
        {"column": "Vendas", "operation": "SUM"},
        source_file="/data/report.xlsx",
        source_hash="abc123",
    )
    assert block.source_file == "/data/report.xlsx"
    assert block.source_hash == "abc123"


def test_datablock_id_is_8_chars(agg, sample_df):
    block = agg.create_block("kpi", sample_df, {"column": "Vendas", "operation": "SUM"})
    assert len(block.block_id) == 8

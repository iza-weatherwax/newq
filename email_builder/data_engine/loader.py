"""
data_engine/loader.py — Carrega arquivos de dados em DataFrames pandas.
Armazena caminho e hash SHA-256 do arquivo para rastreabilidade.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv"}


class DataLoader:
    def __init__(self, path: str) -> None:
        self.source_path = str(Path(path).resolve())
        self.source_hash = self._compute_hash(path)

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def load(self) -> dict[str, pd.DataFrame]:
        """
        Carrega o arquivo e retorna um dicionário {sheet_name: DataFrame}.
        Para CSV/TSV retorna {"Sheet1": DataFrame}.
        """
        path = Path(self.source_path)
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Formato não suportado: '{ext}'. Use: {SUPPORTED_EXTENSIONS}")

        if ext in {".xlsx", ".xls"}:
            return self._load_excel(path)
        else:
            return self._load_flat(path, ext)

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #

    def _load_excel(self, path: Path) -> dict[str, pd.DataFrame]:
        xl = pd.ExcelFile(path, engine="openpyxl" if path.suffix == ".xlsx" else None)
        sheets: dict[str, pd.DataFrame] = {}
        for name in xl.sheet_names:
            df = xl.parse(name)
            sheets[name] = self._clean_df(df)
        return sheets

    def _load_flat(self, path: Path, ext: str) -> dict[str, pd.DataFrame]:
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, encoding="utf-8-sig")
        return {"Sheet1": self._clean_df(df)}

    @staticmethod
    def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
        """Remove colunas totalmente vazias e resets índice."""
        df = df.dropna(axis=1, how="all")
        df = df.reset_index(drop=True)
        return df

    @staticmethod
    def _compute_hash(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

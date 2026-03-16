"""
layout_manager/manager.py — Salva e carrega layouts em JSON.
Inclui migração automática de schema entre versões.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from email_builder.models import Layout, BlockConfig, LayoutMeta

CURRENT_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Migradores — adicionar aqui ao evoluir o schema
# ---------------------------------------------------------------------------

def _migrate_1_0_to_1_1(data: dict) -> dict:  # exemplo para versões futuras
    """Placeholder de migração de 1.0 → 1.1."""
    data["_meta"]["version"] = "1.1"
    return data


MIGRATORS: dict[tuple[str, str], Callable[[dict], dict]] = {
    # ("1.0", "1.1"): _migrate_1_0_to_1_1,  # ativar quando houver v1.1
}


def _migrate_layout(data: dict) -> dict:
    """Aplica migrações sequenciais até atingir CURRENT_VERSION."""
    version = data.get("_meta", {}).get("version", "1.0")
    versions = [v[0] for v in MIGRATORS] + [CURRENT_VERSION]
    while version != CURRENT_VERSION:
        next_versions = [v[1] for v in MIGRATORS if v[0] == version]
        if not next_versions:
            break
        target = next_versions[0]
        migrator = MIGRATORS.get((version, target))
        if migrator:
            data = migrator(data)
        version = target
    return data


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def save_layout(path: str | Path, layout: Layout) -> None:
    """Serializa um Layout para JSON no caminho especificado."""
    layout.meta.saved_at = datetime.now(timezone.utc).isoformat()
    layout.meta.block_count = len(layout.blocks)
    layout.meta.version = CURRENT_VERSION

    Path(path).write_text(
        json.dumps(layout.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_layout(path: str | Path) -> Layout:
    """Carrega um JSON de layout, migrando o schema se necessário."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)

    if "_meta" not in data:
        data["_meta"] = {}

    data = _migrate_layout(data)
    return Layout.from_dict(data)


def empty_layout() -> Layout:
    """Retorna um layout vazio pronto para uso."""
    return Layout(meta=LayoutMeta(), blocks=[])

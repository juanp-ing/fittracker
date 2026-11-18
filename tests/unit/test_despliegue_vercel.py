"""Preparación para Vercel: Postgres (Neon), punto de entrada y seed seguro en producción."""

import importlib
from pathlib import Path

import pytest

from app.config.settings import normalizar_url_bd

RAIZ = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "entrada, esperada",
    [
        # Neon / Vercel entregan postgres:// o postgresql://; SQLAlchemy necesita el driver psycopg 3.
        ("postgres://u:p@h/db?sslmode=require", "postgresql+psycopg://u:p@h/db?sslmode=require"),
        ("postgresql://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("sqlite:///x.db", "sqlite:///x.db"),
        (None, None),
        ("", None),
    ],
)
def test_normaliza_la_url_de_postgres(entrada, esperada):
    assert normalizar_url_bd(entrada) == esperada


def test_produccion_usa_database_url_normalizada(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    import app.config.settings as settings

    recargado = importlib.reload(settings)
    try:
        assert recargado.ProductionConfig.SQLALCHEMY_DATABASE_URI == "postgresql+psycopg://u:p@h/db"
        # Conexiones que Neon cierra por inactividad: comprobarlas antes de usarlas.
        assert recargado.ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS["pool_pre_ping"] is True
    finally:
        monkeypatch.delenv("DATABASE_URL")
        importlib.reload(settings)


def test_hay_punto_de_entrada_para_vercel():
    fuente = (RAIZ / "index.py").read_text(encoding="utf-8")
    assert "create_app(" in fuente
    # En serverless el seed no corre en cada arranque en frío: va en «flask seed».
    assert "seed_database" not in fuente
    assert "create_all" not in fuente


def test_psycopg_en_dependencias():
    assert "psycopg[binary]" in (RAIZ / "requirements.txt").read_text(encoding="utf-8")


def test_la_base_local_y_los_tests_no_se_suben_a_vercel():
    ignorados = (RAIZ / ".vercelignore").read_text(encoding="utf-8").split()
    for patron in ("*.db", ".venv", "tests", ".env"):
        assert patron in ignorados, patron


def test_el_seed_nunca_borra_tablas_fuera_de_sqlite():
    fuente = (RAIZ / "app" / "seeds" / "initial_data.py").read_text(encoding="utf-8")
    bloque = fuente[fuente.index("db.drop_all()") - 400 : fuente.index("db.drop_all()")]
    assert 'dialect.name == "sqlite"' in bloque

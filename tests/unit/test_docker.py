"""El contenedor arranca de forma fiable y no mete archivos locales en la imagen."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_gunicorn_carga_la_app_una_sola_vez():
    # Sin --preload cada worker ejecutaba run.py (tablas + seed) a la vez sobre el mismo SQLite:
    # el primer arranque fallaba o duplicaba el catálogo.
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    cmd = next(linea for linea in dockerfile.splitlines() if linea.startswith("CMD"))
    assert '"--preload"' in cmd


def test_la_imagen_no_incluye_bases_entornos_ni_secretos():
    ignorados = (RAIZ / ".dockerignore").read_text(encoding="utf-8").split()
    for patron in ("*.db", ".venv", ".env", ".env.*", ".git", ".vercel"):
        assert patron in ignorados, patron


def test_hay_plantilla_de_env_con_secret_key():
    plantilla = (RAIZ / ".env.example").read_text(encoding="utf-8")
    assert "SECRET_KEY=" in plantilla
    compose = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")
    assert "SECRET_KEY=${SECRET_KEY:?" in compose

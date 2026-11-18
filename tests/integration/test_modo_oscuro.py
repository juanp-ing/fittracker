"""Modo oscuro (paleta oscura de Duolingo): tokens, activación sin parpadeo y selector en Perfil."""

from sqlalchemy.orm import close_all_sessions
import re
from pathlib import Path

import pytest

from app import create_app, db
from app.seeds.initial_data import seed_database

CSS = (Path(__file__).resolve().parents[2] / "app" / "static" / "css" / "styles.css").read_text()


def _bloque(selector: str) -> dict[str, str]:
    """Tokens --color-* declarados en el primer bloque que abre con ``selector``."""
    inicio = CSS.index(selector + " {")
    cuerpo = CSS[inicio : CSS.index("}", inicio)]
    return dict(re.findall(r"(--color-[\w-]+):\s*([^;]+);", cuerpo))


@pytest.fixture()
def client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_database(incluir_demo=False)
        cliente = app.test_client()
        resp = cliente.post(
            "/api/auth/register",
            json={"nombre": "Noche", "email": "noche@fittracker.local", "password": "Password123!"},
        )
        yield cliente
        db.session.remove()
        close_all_sessions()  # Postgres: ninguna sesión abierta puede bloquear el DROP
        db.drop_all()


def test_el_texto_sobre_botones_de_color_usa_su_propio_token():
    # paper-white es la superficie: en oscuro se vuelve casi negra y no puede ser el texto del botón.
    assert not re.search(r"^\s*color:\s*var\(--color-paper-white\)", CSS, re.M)
    assert _bloque(":root")["--color-on-accent"].strip() == "#ffffff"


def test_tema_oscuro_automatico_y_forzado_declaran_los_mismos_tokens():
    auto = _bloque('  :root:not([data-theme="light"])')
    forzado = _bloque(':root[data-theme="dark"]')
    assert auto and auto == forzado
    claros = _bloque(":root")
    # Todo token de color que cambia de aspecto tiene valor oscuro.
    for token in ("--color-paper-white", "--color-night-ink", "--color-charcoal", "--color-surface-muted",
                  "--color-faded-gray", "--color-border-light", "--color-on-accent", "--color-eager-green"):
        assert token in auto and auto[token] != claros[token], token
    assert auto["--color-paper-white"].strip() == "#131f24"  # fondo oscuro de Duolingo
    assert "@media (prefers-color-scheme: dark)" in CSS
    assert re.search(r"color-scheme:\s*dark", CSS)


def test_base_aplica_el_tema_guardado_antes_de_la_hoja_de_estilos(client):
    html = client.get("/").get_data(as_text=True)
    script = html.index("fittracker_tema")
    assert script < html.index("css/styles.css"), "el tema debe fijarse antes de pintar"
    assert re.search(r'<meta name="theme-color" content="#58cc02" media="\(prefers-color-scheme: light\)">', html)
    assert re.search(r'<meta name="theme-color" content="#131f24" media="\(prefers-color-scheme: dark\)">', html)


def test_perfil_tiene_selector_de_tema(client):
    html = client.get("/perfil").get_data(as_text=True)
    opciones = re.findall(r'data-tema-opcion="(\w+)"', html)
    assert opciones == ["auto", "light", "dark"]

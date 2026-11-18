"""Hoy sin rutina no inventa días de entreno y el editor de rutinas tiene buscador.

Auditoría funcional del 2026-11-18:
- Un usuario sin rutina veía lun/mié/vie marcados como «toca entrenar» y, a la vez,
  «Entrenamiento libre» y «No hay ejercicios planificados».
- Al crear una rutina, los ejercicios se elegían en un <select> de 104 opciones sin búsqueda.
"""

import json
import re

import pytest

from app import create_app, db
from app.seeds.initial_data import seed_database


@pytest.fixture()
def client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_database(incluir_demo=False)
        cliente = app.test_client()
        resp = cliente.post(
            "/api/auth/register",
            json={"nombre": "Sin Rutina", "email": "sinrutina@fittracker.local", "password": "Password123!"},
        )
        codigo = resp.get_json()["codigo_verificacion"]
        assert cliente.post("/api/auth/verify-code", json={"codigo": codigo}).status_code == 200
        yield cliente
        db.session.remove()
        db.drop_all()


def _crear_rutina(client):
    ej = client.get("/api/ejercicios").get_json()["ejercicios"][0]
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Full Body",
            "es_favorita": True,
            "dias_semana": "LUN,MIE,VIE",
            "ejercicios": [{"ejercicio_id": ej["id"], "orden": 1, "series_objetivo": 3, "descanso_segundos": 90}],
        },
    )
    assert resp.status_code == 201


def _leyenda_toca(html: str) -> str:
    m = re.search(r'<span id="leyenda-toca-entrenar"[^>]*>', html)
    assert m, "falta la leyenda «Toca entrenar» con id"
    return m.group(0)


# ---------------------------------------------------------------- Hoy sin rutina


def test_sin_rutina_ningun_dia_toca_entrenar(client):
    agenda = client.get("/api/sesiones/agenda-diaria?fecha=2026-11-18").get_json()
    assert agenda["rutina"] is None
    assert [d["toca_entrenar"] for d in agenda["dias_semana"]] == [False] * 7
    assert [d["puntos"] for d in agenda["dias_semana"]] == [0] * 7


def test_sin_rutina_hoy_oculta_leyenda_y_enlaza_a_rutinas(client):
    html = client.get("/").get_data(as_text=True)
    assert "calendar-dot--plan" not in html.split('id="leyenda-toca-entrenar"')[0]
    assert "hidden" in _leyenda_toca(html)
    aviso = html.split('id="checklist-sin-rutina"', 1)[1].split("</p>", 1)[0]
    assert 'href="/rutinas"' in aviso


def test_con_rutina_la_leyenda_toca_entrenar_se_ve(client):
    _crear_rutina(client)
    html = client.get("/").get_data(as_text=True)
    assert "hidden" not in _leyenda_toca(html)
    agenda = client.get("/api/sesiones/agenda-diaria?fecha=2026-11-18").get_json()
    assert [d["codigo_dia"] for d in agenda["dias_semana"] if d["toca_entrenar"]] == ["LUN", "MIE", "VIE"]


# ---------------------------------------------------------- buscador del editor


def test_editor_de_rutinas_usa_buscador_en_vez_de_select(client):
    html = client.get("/rutinas").get_data(as_text=True)
    assert 'id="rutina-ejercicio-select"' not in html
    assert 'id="btn-agregar-ej-rutina"' not in html
    assert re.search(r'<input[^>]+id="rutina-ejercicio-buscar"[^>]+type="search"', html)
    assert 'id="rutina-ejercicio-resultados"' in html


def test_editor_trae_el_catalogo_completo_y_los_grupos_para_filtrar(client):
    html = client.get("/rutinas").get_data(as_text=True)
    m = re.search(r'<script type="application/json" id="datos-catalogo-rutina">(.*?)</script>', html, re.S)
    assert m, "falta el catálogo embebido para el buscador"
    catalogo = json.loads(m.group(1))
    total = len(client.get("/api/ejercicios").get_json()["ejercicios"])
    assert len(catalogo) == total
    assert {"id", "nombre", "grupo", "grupos"} <= set(catalogo[0])

    chips = re.findall(r'data-filtro-grupo="([^"]*)"', html)
    grupos = {e["grupo"] for e in catalogo}
    assert set(chips) == grupos

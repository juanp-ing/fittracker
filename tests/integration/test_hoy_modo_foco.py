"""Pruebas de la pantalla "Hoy" en dos estados (antes de entrenar / modo foco) y deshacer serie."""

import json
import re
from datetime import datetime, timedelta, timezone

from app import db
from app.models.pr import PR
from app.models.sesion import Serie, Sesion
from app.seeds import seed_database


def _usuario(client, email="foco@fittracker.local"):
    resp = client.post(
        "/api/auth/register",
        json={"nombre": "Atleta Foco", "email": email, "password": "Password123!"},
    )
    assert resp.status_code == 201
    client.post(
        "/api/auth/verify-code", json={"codigo": resp.get_json()["codigo_verificacion"]}
    )
    return resp.get_json()["id"]


def _rutina(client, ejercicios):
    """Crea una rutina favorita para todos los días con [(ejercicio_id, series, descanso)]."""
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Rutina Foco",
            "es_favorita": True,
            "dias_semana": "LUN,MAR,MIE,JUE,VIE,SAB,DOM",
            "ejercicios": [
                {
                    "ejercicio_id": ej,
                    "orden": i + 1,
                    "series_objetivo": series,
                    "descanso_segundos": descanso,
                }
                for i, (ej, series, descanso) in enumerate(ejercicios)
            ],
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _catalogo(client):
    return client.get("/api/ejercicios").get_json()["ejercicios"]


def _serie(client, sesion_id, ejercicio_id, peso=40, reps=10):
    resp = client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={"ejercicio_id": ejercicio_id, "peso": peso, "repeticiones": reps},
    )
    assert resp.status_code == 201
    return resp.get_json()


def _datos_sesion_activa(html):
    """Extrae el JSON embebido con la sesión activa que la vista entrega al JS."""
    m = re.search(
        r'<script type="application/json" id="datos-sesion-activa">(.*?)</script>', html, re.S
    )
    assert m, "La vista Hoy debe embeber #datos-sesion-activa"
    return json.loads(m.group(1))


def _modo(html):
    return re.search(r'id="vista-hoy"[^>]*data-modo="(\w+)"', html).group(1)


# --------------------------------------------------------------------------------------
# Estado inicial de la vista según la sesión activa del servidor (no de localStorage)
# --------------------------------------------------------------------------------------


def test_sin_sesion_activa_la_vista_hoy_arranca_antes_de_entrenar(app, client):
    seed_database()
    _usuario(client)

    html = client.get("/").get_data(as_text=True)

    assert _modo(html) == "previo"
    assert _datos_sesion_activa(html) is None
    assert 'id="btn-empezar-entrenamiento"' in html


def test_con_sesion_activa_reciente_la_vista_hoy_arranca_en_modo_foco_con_sus_series(
    app, client
):
    seed_database()
    _usuario(client)
    ej = _catalogo(client)[0]["id"]
    sesion = client.post("/api/sesiones", json={}).get_json()
    _serie(client, sesion["id"], ej, peso=40)
    _serie(client, sesion["id"], ej, peso=42.5)

    html = client.get("/").get_data(as_text=True)

    assert _modo(html) == "foco"
    datos = _datos_sesion_activa(html)
    assert datos["id"] == sesion["id"]
    assert [s["peso"] for s in datos["series"]] == [40, 42.5]
    assert all(s["ejercicio_nombre"] for s in datos["series"])
    assert {"id", "ejercicio_id", "repeticiones", "es_pr"} <= set(datos["series"][0])


def test_sesion_activa_abandonada_hace_mas_de_12_horas_no_se_retoma(app, client):
    seed_database()
    _usuario(client)
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    sesion = db.session.get(Sesion, sesion_id)
    sesion.fecha_inicio = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=13)
    db.session.commit()

    html = client.get("/").get_data(as_text=True)

    assert _modo(html) == "previo"
    assert _datos_sesion_activa(html) is None


def test_sesion_finalizada_no_se_retoma(app, client):
    seed_database()
    _usuario(client)
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    client.patch(f"/api/sesiones/{sesion_id}/finalizar")

    assert _modo(client.get("/").get_data(as_text=True)) == "previo"


# --------------------------------------------------------------------------------------
# Deshacer (borrar) una serie
# --------------------------------------------------------------------------------------


def test_deshacer_serie_la_elimina_junto_con_su_pr(app, client):
    seed_database()
    _usuario(client)
    ej = _catalogo(client)[0]["id"]
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    _serie(client, sesion_id, ej, peso=40)
    ultima = _serie(client, sesion_id, ej, peso=50)
    assert ultima["es_pr"] is True

    resp = client.delete(f"/api/sesiones/{sesion_id}/series/{ultima['id']}")

    assert resp.status_code == 200
    cuerpo = resp.get_json()
    assert cuerpo["serie_id"] == ultima["id"]
    assert cuerpo["series_completadas_ejercicio"] == 1
    assert db.session.get(Serie, ultima["id"]) is None
    assert db.session.query(PR).filter_by(serie_id=ultima["id"]).count() == 0
    # Tras deshacer, 45 kg vuelve a ser récord frente a los 40 kg que quedan
    assert _serie(client, sesion_id, ej, peso=45)["es_pr"] is True


def test_no_se_puede_borrar_una_serie_de_otro_usuario(app, client):
    seed_database()
    _usuario(client, "duena@fittracker.local")
    ej = _catalogo(client)[0]["id"]
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    serie_id = _serie(client, sesion_id, ej)["id"]
    client.post("/api/auth/logout")

    _usuario(client, "intrusa@fittracker.local")
    resp = client.delete(f"/api/sesiones/{sesion_id}/series/{serie_id}")

    assert resp.status_code == 404
    assert db.session.get(Serie, serie_id) is not None


def test_no_se_puede_borrar_una_serie_de_una_sesion_finalizada(app, client):
    seed_database()
    _usuario(client)
    ej = _catalogo(client)[0]["id"]
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    serie_id = _serie(client, sesion_id, ej)["id"]
    client.patch(f"/api/sesiones/{sesion_id}/finalizar")

    resp = client.delete(f"/api/sesiones/{sesion_id}/series/{serie_id}")

    assert resp.status_code == 400
    assert db.session.get(Serie, serie_id) is not None


def test_borrar_serie_que_no_pertenece_a_esa_sesion_devuelve_404(app, client):
    seed_database()
    _usuario(client)
    ej = _catalogo(client)[0]["id"]
    sesion_a = client.post("/api/sesiones", json={}).get_json()["id"]
    sesion_b = client.post("/api/sesiones", json={}).get_json()["id"]
    serie_id = _serie(client, sesion_a, ej)["id"]

    resp = client.delete(f"/api/sesiones/{sesion_b}/series/{serie_id}")

    assert resp.status_code == 404


# --------------------------------------------------------------------------------------
# Resumen del plan del día para la tarjeta "Hoy toca"
# --------------------------------------------------------------------------------------


def test_agenda_incluye_series_totales_hechas_y_minutos_estimados(app, client):
    seed_database()
    _usuario(client)
    cat = _catalogo(client)
    ej1, ej2 = cat[0]["id"], cat[1]["id"]
    rutina_id = _rutina(client, [(ej1, 3, 90), (ej2, 3, 120)])
    sesion_id = client.post("/api/sesiones", json={"rutina_id": rutina_id}).get_json()["id"]
    _serie(client, sesion_id, ej1)

    agenda = client.get("/api/sesiones/agenda-diaria").get_json()

    assert agenda["series_totales"] == 6
    assert agenda["series_hechas"] == 1
    # 3 × (45 s de trabajo + 90 s) + 3 × (45 s + 120 s) = 900 s = 15 min
    assert agenda["minutos_estimados"] == 15


def test_la_sesion_activa_no_marca_como_record_la_primera_serie_de_un_ejercicio(app, client):
    seed_database()
    _usuario(client)
    ej = _catalogo(client)[0]["id"]
    sesion = client.post("/api/sesiones", json={}).get_json()
    _serie(client, sesion["id"], ej, peso=40)
    _serie(client, sesion["id"], ej, peso=45)

    series = _datos_sesion_activa(client.get("/").get_data(as_text=True))["series"]

    assert [s["es_pr"] for s in series] == [False, True]

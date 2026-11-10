"""Pruebas de regresión para los arreglos rápidos de la auditoría UX/UI.

Cubre: día local según la zona horaria del navegador, PRs agrupados por ejercicio en el
resumen mensual y orden del selector de progreso del mapa por ejercicio más entrenado.
"""

import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app import db
from app.models.sesion import Serie
from app.seeds import seed_database
from app.services.sesion_service import SesionService


def _usuario_verificado(client, email="ux@fittracker.local"):
    """Registra y verifica un usuario; devuelve su id."""
    resp = client.post(
        "/api/auth/register",
        json={"nombre": "Atleta UX", "email": email, "password": "Password123!"},
    )
    assert resp.status_code == 201
    datos = resp.get_json()
    client.post("/api/auth/verify-code", json={"codigo": datos["codigo_verificacion"]})
    return datos["id"]


def _registrar_series(client, ejercicio_id, pesos, rutina_id=None):
    """Abre una sesión y registra una serie de 10 repeticiones por cada peso indicado."""
    sesion = client.post("/api/sesiones", json={"rutina_id": rutina_id}).get_json()
    for peso in pesos:
        resp = client.post(
            f"/api/sesiones/{sesion['id']}/series",
            json={"ejercicio_id": ejercicio_id, "peso": peso, "repeticiones": 10},
        )
        assert resp.status_code == 201
    return sesion["id"]


def _crear_rutina(client, ejercicio_id):
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Rutina Zona Horaria",
            "es_favorita": True,
            "dias_semana": "LUN,MAR,MIE,JUE,VIE,SAB,DOM",
            "ejercicios": [
                {
                    "ejercicio_id": ejercicio_id,
                    "orden": 1,
                    "series_objetivo": 3,
                    "descanso_segundos": 90,
                }
            ],
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


# --------------------------------------------------------------------------------------
# Zona horaria: el "hoy" de la agenda debe ser el día local del usuario, no el de UTC.
# --------------------------------------------------------------------------------------


def test_agenda_marca_como_hoy_el_dia_local_y_no_el_dia_utc(app, client):
    """A las 21:00 en Bogotá (02:00 UTC del día siguiente) hoy sigue siendo el día local."""
    seed_database()
    usuario_id = _usuario_verificado(client)
    ahora = datetime(2026, 11, 5, 2, 0, tzinfo=timezone.utc)  # 4-nov 21:00 en Bogotá

    agenda = SesionService().obtener_agenda_diaria(
        usuario_id=usuario_id,
        zona_horaria="America/Bogota",
        ahora=ahora,
    )

    assert agenda["fecha"] == "2026-11-04"
    dias_hoy = [d["fecha"] for d in agenda["dias_semana"] if d["es_hoy"]]
    assert dias_hoy == ["2026-11-04"]


def test_agenda_cuenta_series_nocturnas_en_el_dia_local(app, client):
    """Una serie guardada a las 02:00 UTC del 5-nov pertenece al 4-nov en Bogotá."""
    seed_database()
    usuario_id = _usuario_verificado(client)
    ejercicio_id = client.get("/api/ejercicios").get_json()["ejercicios"][0]["id"]
    rutina_id = _crear_rutina(client, ejercicio_id)
    _registrar_series(client, ejercicio_id, [40], rutina_id=rutina_id)

    serie = db.session.query(Serie).one()
    serie.fecha_hora = datetime(2026, 11, 5, 2, 0)  # UTC naive, como se persiste
    db.session.commit()

    agenda = SesionService().obtener_agenda_diaria(
        usuario_id=usuario_id,
        fecha_str="2026-11-04",
        zona_horaria="America/Bogota",
        ahora=datetime(2026, 11, 5, 2, 30, tzinfo=timezone.utc),
    )

    item = next(e for e in agenda["ejercicios"] if e["ejercicio_id"] == ejercicio_id)
    assert item["series_completadas_hoy"] == 1
    dia_4 = next(d for d in agenda["dias_semana"] if d["fecha"] == "2026-11-04")
    assert dia_4["series_registradas"] == 1


def test_endpoint_agenda_usa_la_zona_horaria_de_la_cookie(app, client):
    """Kiritimati (UTC+14) y Pago Pago (UTC−11) nunca comparten fecha: la cookie decide."""
    seed_database()
    _usuario_verificado(client)

    fechas = {}
    for tz in ("Pacific/Kiritimati", "Pacific/Pago_Pago"):
        client.set_cookie("ft_tz", tz)
        agenda = client.get("/api/sesiones/agenda-diaria").get_json()
        fechas[tz] = agenda["fecha"]
        assert agenda["fecha"] == datetime.now(ZoneInfo(tz)).date().isoformat()

    assert fechas["Pacific/Kiritimati"] != fechas["Pacific/Pago_Pago"]


def test_zona_horaria_invalida_cae_a_utc_sin_error(app, client):
    seed_database()
    _usuario_verificado(client)
    client.set_cookie("ft_tz", "Marte/Olympus_Mons")

    resp = client.get("/api/sesiones/agenda-diaria")

    assert resp.status_code == 200
    assert resp.get_json()["fecha"] == datetime.now(timezone.utc).date().isoformat()


# --------------------------------------------------------------------------------------
# Resumen mensual: un solo PR por ejercicio y tipo (el mejor), no uno por cada serie.
# --------------------------------------------------------------------------------------


def test_resumen_muestra_un_solo_pr_por_ejercicio_con_el_mejor_peso(app, client):
    seed_database()
    _usuario_verificado(client)
    ejercicio_id = client.get("/api/ejercicios").get_json()["ejercicios"][0]["id"]
    _registrar_series(client, ejercicio_id, [40, 42.5, 45])

    resumen = client.get("/api/resumen-mensual").get_json()

    prs_ejercicio = [p for p in resumen["prs_detalle"] if p["ejercicio_id"] == ejercicio_id]
    tipos = [p["tipo_pr"] for p in prs_ejercicio]
    assert len(tipos) == len(set(tipos)), f"PRs duplicados por tipo: {prs_ejercicio}"
    assert max(p["peso"] for p in prs_ejercicio) == 45
    assert resumen["nuevos_prs"] == len(resumen["prs_detalle"])


# --------------------------------------------------------------------------------------
# Mapa: el selector de progreso empieza por el ejercicio más entrenado.
# --------------------------------------------------------------------------------------


def test_selector_progreso_del_mapa_empieza_por_el_ejercicio_mas_entrenado(app, client):
    seed_database()
    _usuario_verificado(client)
    catalogo = client.get("/api/ejercicios").get_json()["ejercicios"]
    poco_usado, mas_usado = catalogo[3]["id"], catalogo[7]["id"]
    _registrar_series(client, poco_usado, [20])
    _registrar_series(client, mas_usado, [30, 30, 30])

    html = client.get("/mapa").get_data(as_text=True)

    selector = re.search(
        r'<select id="selector-ejercicio-progreso"[^>]*>(.*?)</select>', html, re.S
    ).group(1)
    valores = re.findall(r'<option value="(\d+)"', selector)
    assert valores[:2] == [str(mas_usado), str(poco_usado)]

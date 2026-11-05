"""Pruebas del paso 4 (capa visual): racha semanal, comparativa mensual y primeras marcas."""

from datetime import datetime, timedelta, timezone

from app import db
from app.models.sesion import Serie
from app.seeds import seed_database
from app.services.sesion_service import SesionService

# Miércoles 4-nov-2026 15:00 en Bogotá. La semana de la tira va de domingo 1 a sábado 7.
AHORA = datetime(2026, 11, 4, 20, 0, tzinfo=timezone.utc)
ZONA = "America/Bogota"


def _usuario(client, email="visual@fittracker.local"):
    resp = client.post(
        "/api/auth/register",
        json={"nombre": "Atleta Visual", "email": email, "password": "Password123!"},
    )
    assert resp.status_code == 201
    client.post(
        "/api/auth/verify-code", json={"codigo": resp.get_json()["codigo_verificacion"]}
    )
    return resp.get_json()["id"]


def _catalogo(client):
    return client.get("/api/ejercicios").get_json()["ejercicios"]


def _rutina(client, dias):
    ej = _catalogo(client)[0]["id"]
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": "Rutina Racha",
            "es_favorita": True,
            "dias_semana": dias,
            "ejercicios": [
                {"ejercicio_id": ej, "orden": 1, "series_objetivo": 3, "descanso_segundos": 90}
            ],
        },
    )
    assert resp.status_code == 201


def _series_en_fechas(client, fechas_utc, ejercicio_id=None, peso=40):
    """Registra una serie por fecha (UTC naive) y fija su fecha_hora."""
    ejercicio_id = ejercicio_id or _catalogo(client)[0]["id"]
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    for fecha in fechas_utc:
        serie_id = client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={"ejercicio_id": ejercicio_id, "peso": peso, "repeticiones": 10},
        ).get_json()["id"]
        db.session.get(Serie, serie_id).fecha_hora = fecha
    db.session.commit()


def _dia(y, m, d, hora=17):
    """Mediodía-tarde en Bogotá expresado en UTC naive (17:00 UTC = 12:00 Bogotá)."""
    return datetime(y, m, d, hora, 0)


def _racha(usuario_id):
    return SesionService().obtener_agenda_diaria(
        usuario_id=usuario_id, zona_horaria=ZONA, ahora=AHORA
    )["racha"]


# --------------------------------------------------------------------------------------
# Racha semanal
# --------------------------------------------------------------------------------------


def test_racha_sin_entrenos_y_sin_rutina_usa_meta_de_3_dias(app, client):
    seed_database()
    usuario_id = _usuario(client)

    racha = _racha(usuario_id)

    assert racha == {
        "semanas_seguidas": 0,
        "dias_semana_actual": 0,
        "meta_dias_semana": 3,
        "semana_cumplida": False,
    }


def test_meta_semanal_sale_de_la_rutina_principal(app, client):
    seed_database()
    usuario_id = _usuario(client)
    _rutina(client, "LUN,JUE")

    assert _racha(usuario_id)["meta_dias_semana"] == 2


def test_meta_semanal_tiene_tope_de_5_dias(app, client):
    seed_database()
    usuario_id = _usuario(client)
    _rutina(client, "LUN,MAR,MIE,JUE,VIE,SAB,DOM")

    assert _racha(usuario_id)["meta_dias_semana"] == 5


def test_racha_cuenta_semanas_consecutivas_que_cumplen_la_meta(app, client):
    seed_database()
    usuario_id = _usuario(client)
    _rutina(client, "LUN,JUE")  # meta = 2 días por semana
    _series_en_fechas(
        client,
        [
            _dia(2026, 10, 12), _dia(2026, 10, 15),  # semana 11–17 oct: 2 días
            _dia(2026, 10, 19), _dia(2026, 10, 22),  # semana 18–24 oct: 2 días
            _dia(2026, 10, 26), _dia(2026, 10, 29),  # semana 25–31 oct: 2 días
        ],
    )

    racha = _racha(usuario_id)

    assert racha["semanas_seguidas"] == 3
    assert racha["dias_semana_actual"] == 0
    assert racha["semana_cumplida"] is False


def test_una_semana_por_debajo_de_la_meta_corta_la_racha(app, client):
    seed_database()
    usuario_id = _usuario(client)
    _rutina(client, "LUN,JUE")
    _series_en_fechas(
        client,
        [
            _dia(2026, 10, 12), _dia(2026, 10, 15),  # cumple
            _dia(2026, 10, 19),                      # solo 1 día: corta
            _dia(2026, 10, 26), _dia(2026, 10, 29),  # cumple
        ],
    )

    assert _racha(usuario_id)["semanas_seguidas"] == 1


def test_la_semana_actual_suma_a_la_racha_cuando_ya_cumple(app, client):
    seed_database()
    usuario_id = _usuario(client)
    _rutina(client, "LUN,JUE")
    _series_en_fechas(
        client,
        [
            _dia(2026, 10, 26), _dia(2026, 10, 29),  # semana pasada
            _dia(2026, 11, 2), _dia(2026, 11, 3),    # esta semana: lun y mar
            _dia(2026, 11, 3, hora=18),              # mismo día: no cuenta doble
        ],
    )

    racha = _racha(usuario_id)

    assert racha["dias_semana_actual"] == 2
    assert racha["semana_cumplida"] is True
    assert racha["semanas_seguidas"] == 2


# --------------------------------------------------------------------------------------
# Resumen mensual: comparativa y primeras marcas
# --------------------------------------------------------------------------------------


def test_resumen_compara_con_los_30_dias_anteriores(app, client):
    seed_database()
    _usuario(client)
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    hace_40 = ahora - timedelta(days=40)
    _series_en_fechas(client, [hace_40, hace_40 + timedelta(minutes=5)], peso=50)  # 1000 kg
    _series_en_fechas(client, [ahora - timedelta(days=2), ahora - timedelta(days=1)], peso=60)  # 1200 kg

    comparativa = client.get("/api/resumen-mensual").get_json()["comparativa"]

    assert comparativa["series"] == 2
    assert comparativa["volumen_kg"] == 1000
    assert comparativa["variacion_volumen_pct"] == 20  # 1200 vs 1000


def test_variacion_es_nula_si_no_hubo_mes_anterior(app, client):
    seed_database()
    _usuario(client)
    _series_en_fechas(client, [datetime.now(timezone.utc).replace(tzinfo=None)])

    comparativa = client.get("/api/resumen-mensual").get_json()["comparativa"]

    assert comparativa["volumen_kg"] == 0
    assert comparativa["variacion_volumen_pct"] is None


def test_la_primera_serie_de_un_ejercicio_es_primera_marca_y_no_record(app, client):
    seed_database()
    _usuario(client)
    cat = _catalogo(client)
    nuevo, progresa = cat[0]["id"], cat[1]["id"]
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    for ej, peso in [(nuevo, 40), (progresa, 50), (progresa, 55)]:
        client.post(
            f"/api/sesiones/{sesion_id}/series",
            json={"ejercicio_id": ej, "peso": peso, "repeticiones": 10},
        )

    resumen = client.get("/api/resumen-mensual").get_json()

    assert [p["ejercicio_id"] for p in resumen["prs_detalle"]] == [progresa]
    assert resumen["nuevos_prs"] == 1
    assert resumen["primeras_marcas"] == 1


def test_grafica_de_progreso_agrupa_por_dia_local(app, client):
    seed_database()
    _usuario(client)
    ej = _catalogo(client)[0]["id"]
    _series_en_fechas(client, [datetime(2026, 11, 5, 2, 0)], ejercicio_id=ej)  # 4-nov 21:00 Bogotá
    client.set_cookie("ft_tz", ZONA)

    progreso = client.get(f"/api/progreso/{ej}").get_json()

    assert progreso["fechas"] == ["2026-11-04"]

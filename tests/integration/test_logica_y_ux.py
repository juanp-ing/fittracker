"""Pruebas de los arreglos de lógica y UX de la auditoría.

Cubre: una sola rutina principal al clonar, meta semanal con todas las principales, cierre
automático de sesiones abandonadas, día de descanso coherente en Hoy, leyenda del calendario,
ventana por defecto del mapa y acceso a /verificar-correo ya verificado.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import db
from app.models.sesion import Serie, Sesion
from app.seeds import seed_database
from app.services.sesion_service import SesionService

ESTATICOS = Path(__file__).resolve().parents[2] / "app" / "static"
# 2026-11-10 es martes.
MARTES = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)


def _usuario(client, email="logica@fittracker.local", verificar=True):
    resp = client.post(
        "/api/auth/register",
        json={"nombre": "Atleta Lógica", "email": email, "password": "Password123!"},
    )
    assert resp.status_code == 201
    if verificar:
        client.post(
            "/api/auth/verify-code", json={"codigo": resp.get_json()["codigo_verificacion"]}
        )
    return resp.get_json()["id"]


def _ejercicio(client):
    return client.get("/api/ejercicios?q=press").get_json()["ejercicios"][0]["id"]


def _rutina(client, dias, favorita=True, nombre="Rutina"):
    resp = client.post(
        "/api/rutinas",
        json={
            "nombre": nombre,
            "es_favorita": favorita,
            "dias_semana": dias,
            "ejercicios": [{"ejercicio_id": _ejercicio(client), "orden": 1, "series_objetivo": 3}],
        },
    )
    assert resp.status_code == 201
    return resp.get_json()


# ---------------------------------------------------------------- rutina principal
def test_clonar_solo_marca_principal_si_no_habia_ninguna(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    famosas = client.get("/api/rutinas/famosas").get_json()["rutinas_famosas"]

    primera = client.post(f"/api/rutinas/famosas/{famosas[0]['id']}/clonar").get_json()
    segunda = client.post(f"/api/rutinas/famosas/{famosas[1]['id']}/clonar").get_json()

    assert primera["es_favorita"] is True
    assert segunda["es_favorita"] is False
    principales = [r for r in client.get("/api/rutinas").get_json()["rutinas"] if r["es_favorita"]]
    assert [r["id"] for r in principales] == [primera["id"]]


def test_meta_semanal_suma_los_dias_de_todas_las_principales(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    _rutina(client, "LUN,JUE", nombre="Empuje")
    _rutina(client, "MAR,VIE", nombre="Tirón")
    _rutina(client, "SAB,DOM", favorita=False, nombre="Extra")

    agenda = client.get("/api/sesiones/agenda-diaria").get_json()
    assert agenda["racha"]["meta_dias_semana"] == 4


# ---------------------------------------------------------------- sesiones abandonadas
def test_sesion_activa_abandonada_se_cierra_sola(app, client):
    with app.app_context():
        seed_database()
    usuario_id = _usuario(client)
    ejercicio_id = _ejercicio(client)
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]
    client.post(
        f"/api/sesiones/{sesion_id}/series",
        json={"ejercicio_id": ejercicio_id, "peso": 50, "repeticiones": 8},
    )
    vacia_id = client.post("/api/sesiones", json={}).get_json()["id"]

    hace_un_dia = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=26)
    with app.app_context():
        for sid in (sesion_id, vacia_id):
            db.session.get(Sesion, sid).fecha_inicio = hace_un_dia
        ultima = hace_un_dia + timedelta(minutes=40)
        db.session.query(Serie).filter_by(sesion_id=sesion_id).update({"fecha_hora": ultima})
        db.session.commit()

    assert "datos-sesion-activa\">null<" in client.get("/").get_data(as_text=True)

    with app.app_context():
        cerrada = db.session.get(Sesion, sesion_id)
        assert cerrada.estado == "FINALIZADA"
        assert cerrada.fecha_fin == ultima  # termina con su última serie, no «ahora»
        assert len(cerrada.series) == 1
        # Una sesión abandonada sin series no aporta nada al historial: se elimina.
        assert db.session.get(Sesion, vacia_id) is None
        assert SesionService().obtener_sesion_activa(usuario_id) is None


def test_sesion_activa_reciente_no_se_cierra(app, client):
    with app.app_context():
        seed_database()
    usuario_id = _usuario(client)
    sesion_id = client.post("/api/sesiones", json={}).get_json()["id"]

    client.get("/")
    client.post("/api/sesiones", json={})  # iniciar otra tampoco cierra las vigentes
    with app.app_context():
        assert db.session.get(Sesion, sesion_id).estado == "ACTIVA"
        assert SesionService().obtener_sesion_activa(usuario_id) is not None


# ---------------------------------------------------------------- día de descanso
def test_dia_de_descanso_no_invita_a_empezar_como_si_tocara(app, client):
    with app.app_context():
        seed_database()
        _usuario(client)
        _rutina(client, "LUN,MIE,VIE", nombre="Full Body")
        agenda = SesionService().obtener_agenda_diaria(
            usuario_id=1, ahora=MARTES
        )
        assert next(d for d in agenda["dias_semana"] if d["seleccionado"])["toca_entrenar"] is False

    html = client.get("/").get_data(as_text=True)
    js = (ESTATICOS / "js" / "registro.js").read_text(encoding="utf-8")
    assert "Entrenar de todos modos" in js and "Día de descanso" in js
    assert "Entrenar de todos modos" in html or "Hoy toca" in html  # según el día real


def test_calendario_semanal_explica_sus_puntos(app, client):
    with app.app_context():
        seed_database()
    _usuario(client)
    _rutina(client, "LUN,MAR,MIE,JUE,VIE,SAB,DOM")

    html = client.get("/").get_data(as_text=True)
    assert 'class="calendar-legend"' in html
    assert "Toca entrenar" in html and "Entrenado" in html
    assert "calendar-dot calendar-dot--plan" in html  # día planificado aún sin entrenar

    js = (ESTATICOS / "js" / "registro.js").read_text(encoding="utf-8")
    assert "calendar-dot--plan" in js


# ---------------------------------------------------------------- mapa y verificación
def test_mapa_elige_la_ventana_mas_corta_con_datos(app, client):
    js = (ESTATICOS / "js" / "mapa.js").read_text(encoding="utf-8")
    assert "cargarVentanaInicial" in js
    assert "cargarMapaMuscular(7);\n    }\n  });" not in js


def test_verificar_correo_redirige_si_ya_esta_verificado(app, client):
    with app.app_context():
        seed_database()
    _usuario(client, verificar=False)
    assert client.get("/verificar-correo").status_code == 200

    codigo = client.post("/api/auth/resend-code").get_json()["codigo_verificacion"]
    client.post("/api/auth/verify-code", json={"codigo": codigo})
    resp = client.get("/verificar-correo")
    assert resp.status_code == 302
    assert "verificar-correo" not in resp.headers["Location"]
